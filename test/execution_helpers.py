"""Exercise application policies through the real shared execution entry."""
from types import SimpleNamespace

from infermatrix_copilot.app.workflow_execution import WorkflowExecution


def application_executor(registry, settings, *, run_dir, **resources):
    execution = WorkflowExecution(settings, registry)

    async def run(playbook, state):
        return await execution.execute(playbook, run_dir=run_dir, state=state, **resources)

    return SimpleNamespace(run=run)
