from models.deoldify import colorize as deoldify_model
from models.flux import colorize as flux_model
from models.zhang import colorize as zhang_model
from services.storage_manager import save_output


def _run_model(model_name, model, image_path):
    label = {"zhang": "Zhang", "deoldify": "DeOldify", "flux": "FLUX"}[model_name]
    print(f"[Pipeline] {label} started for {image_path}", flush=True)
    try:
        result = model(image_path)

        if model_name == "flux":
            try:
                result = result[0][0]["image"]
            except (IndexError, KeyError, TypeError) as error:
                raise ValueError("Invalid FLUX output") from error

        if not isinstance(result, str) or not result:
            raise ValueError(f"Invalid {model_name} output")

        saved_path = save_output(result, model_name)
        print(f"[Pipeline] {label} completed: {saved_path}", flush=True)
        return {
            "status": "completed",
            "path": saved_path,
        }
    except Exception as error:
        print(f"[Pipeline] {label} failed: {error}", flush=True)
        return {
            "status": "failed",
            "error": str(error),
        }


def run_all_models(image_path, on_model_complete=None):
    """Run each model sequentially while preserving successful partial results."""
    models = (
        ("zhang", zhang_model),
        ("deoldify", deoldify_model),
        ("flux", flux_model),
    )
    results = {}

    for model_name, model in models:
        results[model_name] = _run_model(model_name, model, image_path)
        if on_model_complete:
            on_model_complete(model_name, results[model_name], dict(results))

    return results
