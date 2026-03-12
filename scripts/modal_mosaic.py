import modal


def download_boltz2():
    from mosaic.models.boltz2 import Boltz2

    Boltz2()


### Build modal image: install mosaic + deps and download boltz2 model.
image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git")
    .run_commands("git clone https://github.com/escalante-bio/mosaic.git")
    .workdir("mosaic")
    .run_commands("uv pip install --system -r pyproject.toml")
    .run_commands("uv pip install --system jax[cuda]")
    .run_commands("uv pip install --system .")
    .run_function(
        download_boltz2
    )  # I'm told it's better to put this on a volume, but this is easy.
    .run_commands("uv pip install --system equinox")
    .env(
        {"XLA_PYTHON_CLIENT_MEM_FRACTION": "0.95"}
    )  # this is a very large binder + target
)
app = modal.App("hallucinate", image=image)


BINDER_LENGTH = 72
TARGET_SEQUENCE = "SLLEFGKMILEETGKLAIPSYSSYGCYCGWGGKGTPKDATDRCCFVHDCCYGNLPDCNPKSDRYKYKRVNGAIVCEKGTSCENRICECDKAAAICFRQNLNTYSKKYMLYPDFLCKGELKC"


@app.function(
    gpu="B200",
    timeout=int(10 * 60 * 60),
    volumes={
        "/structures": modal.Volume.from_name("nipah-binders", create_if_missing=True)
    },
)
def design(max_runtime_seconds: int):
    import uuid
    import time

    import jax
    import jax.numpy as jnp
    import equinox as eqx
    import numpy as np

    from mosaic.models.boltz2 import Boltz2
    import mosaic.losses.structure_prediction as sp
    from mosaic.common import TOKENS
    from mosaic.losses.protein_mpnn import InverseFoldingSequenceRecovery
    from mosaic.losses.transformations import NoCys
    from mosaic.proteinmpnn.mpnn import load_mpnn_sol
    from mosaic.structure_prediction import TargetChain
    from mosaic.optimizers import simplex_APGM

    worker_id = str(uuid.uuid4())[:8]
    # load models
    folder = Boltz2()
    mpnn = load_mpnn_sol(0.05)

    # construct a bias with zeros for the target and -inf for Cys in the binder for MPNN
    bias = (
        jnp.zeros((BINDER_LENGTH, 20)).at[:BINDER_LENGTH, TOKENS.index("C")].set(-1e6)
    )

    # construct the loss function. in practice these weights are found by manual hyperparameter search; e.g. generating designs and checking filter pass rates.
    sp_loss = (
        sp.BinderTargetContact()
        + sp.WithinBinderContact()
        # This is the only novel (relative to BindCraft) term in our loss: it encourages sequences that are _recovered_ by inverse folding (after folding). This correlates with nice qualities (expression, stability, etc), but might make hallucination less likely to go off the rails. The weight here is probably a bit high (judging by the frequency of homopolymers in designs).
        + 10.0 * InverseFoldingSequenceRecovery(mpnn, temp=jnp.array(0.001), bias=bias)
        + 0.05 * sp.TargetBinderPAE()
        + 0.05 * sp.BinderTargetPAE()
        + 0.025 * sp.IPTMLoss()
        + 0.4 * sp.WithinBinderPAE()
        + 0.025 * sp.pTMEnergy()
        + 0.1 * sp.PLDDTLoss()
    )

    features, _ = boltz_features, boltz_writer = folder.binder_features(
        binder_length=BINDER_LENGTH,
        chains=[TargetChain(sequence=TARGET_SEQUENCE, use_msa=True)],
        # Adaptyv probably didn't use a template for the target, so we don't either.
    )

    loss = NoCys(  # wrap loss to ignore Cys residues (by precomposing with a transform that inserts zeros at Cys positions)
        folder.build_multisample_loss(
            loss=sp_loss,
            features=features,
            recycling_steps=1,
            num_samples=4,  # four diffusion model samples to reduce variance. much cheaper than re-running whole model four times.
        )
    )

    @eqx.filter_jit
    def evaluate_loss(loss, pssm, key):
        return loss(pssm, key=key)

    def design():
        # sample a new sequence by optimizing the loss from a random initialization
        _pssm = np.random.uniform(low=0.25, high=0.75) * jax.random.gumbel(
            key=jax.random.key(np.random.randint(10000000)),
            shape=(BINDER_LENGTH, 19),  # 20 amino acids minus Cys
        )

        # get an initial, "soft" (non-sparse) PSSM
        _, pssm = simplex_APGM(
            loss_function=loss,
            x=jax.nn.softmax(_pssm),
            n_steps=100,
            stepsize=0.2 * np.sqrt(BINDER_LENGTH),
            momentum=0.3,
            scale=1.00,
            logspace=False,
            max_gradient_norm=1.0,
        )
        # try to sharpen the PSSM into a discrete sequence (e.g. a one-hot PSSM)
        pssm, _ = simplex_APGM(
            loss_function=loss,
            x=jnp.log(pssm + 1e-5),
            n_steps=50,
            stepsize=0.5 * np.sqrt(BINDER_LENGTH),
            momentum=0.0,
            scale=1.25,  # corresponds to negative entropic regularization -> encourages sparsity
            logspace=True,
            max_gradient_norm=1.0,
        )
        pssm, _ = simplex_APGM(
            loss_function=loss,
            x=jnp.log(pssm + 1e-5),
            n_steps=15,
            stepsize=0.5 * np.sqrt(BINDER_LENGTH),
            momentum=0.0,
            scale=1.4,
            logspace=True,
            max_gradient_norm=1.0,
        )
        # reinsert a Cys row (with zeros) into the PSSM
        pssm = NoCys.sequence(pssm)
        # compute the final sequence by taking the argmax
        seq = pssm.argmax(-1)

        # repredict with full sequence information: during design we use features for X residues in the binder (except for the sequence channel) to make the objective function differentiable (and avoid JIT issues). Now we construct features with full all-atom information. Interestingly this rarely has a large effect.
        seq_str = "".join(TOKENS[i] for i in seq)
        boltz_features, boltz_writer = folder.target_only_features(
            chains=[
                TargetChain(sequence=seq_str, use_msa=False),
                TargetChain(sequence=TARGET_SEQUENCE, use_msa=True),
            ]
        )

        # We rank with a very simple loss function: IPTM + IPSAE. Why not optimize this directly? It's a difficult objective because the gradients are very unreliable, but even if we could we'd likely get designs that wouldn't work in practice.
        ranking_loss = folder.build_multisample_loss(
            loss=1.00 * sp.IPTMLoss()
            + 0.5 * sp.TargetBinderIPSAE()
            + 0.5 * sp.BinderTargetIPSAE(),
            features=boltz_features,
            recycling_steps=3,
            num_samples=6,  # Six diffusion samples to reduce variance in ranking.
        )

        loss_value, _ = evaluate_loss(
            ranking_loss, jax.nn.one_hot(seq, 20), key=jax.random.key(0)
        )

        return (seq_str, loss_value.item())

    start_time = time.time()
    results = []
    while time.time() - start_time < max_runtime_seconds:
        seq, loss_value = design()
        with open(
            f"/structures/designs_{worker_id}.txt", "a"
        ) as f:  # in case the run dies
            f.write(f">{loss_value:.4f}\n{seq}\n")
        results.append((seq, loss_value))

    return results


@app.local_entrypoint()
def main(max_time_hours: float, workers: int, output_path: str = "designs.txt"):
    arguments = [max_time_hours * 60 * 60 for _ in range(workers)]
    all_results = sorted(sum(design.map(arguments), []), key=lambda x: x[1])
    with open(output_path, "w") as f:
        for idx, (seq, loss_value) in enumerate(all_results):
            f.write(f">design{idx}_{loss_value:.4f}\n{seq}\n")
