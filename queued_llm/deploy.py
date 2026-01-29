"""Deploy the chat completion flow to a Prefect work pool."""

from prefect import deploy

from flows import chat_completion_pipeline

if __name__ == "__main__":
    deploy(
        chat_completion_pipeline.to_deployment(
            name="chat-completion-deployment",
            work_pool_name="llm-pool",
            job_variables={"env": {"DATABASE_URL": "sqlite+aiosqlite:///./queued_llm/jobs.db"}},
        ),
    )
    print("Deployed chat_completion_pipeline to work pool 'llm-pool'")
