from dotenv import load_dotenv

from ai.headline_generator import (
    ResumeHeadlineGenerator,
    load_headline_inputs_from_env,
)
from logs.logger_config import setup_logger


load_dotenv()
logger = setup_logger()


def main() -> None:
    inputs = load_headline_inputs_from_env()

    if not inputs:
        raise ValueError(
            "Cannot generate headline. Add RESUME_TEXT or RESUME_TEXT_PATH, "
            "TECH_STACK, EXPERIENCE, TARGET_ROLE, and at least one provider key "
            "to .env."
        )

    generator = ResumeHeadlineGenerator()
    generator.validate_inputs(inputs)
    try:
        result = generator.generate(inputs)
    except Exception as error:
        logger.error(f"Headline generation failed: {error}")
        raise

    print("\nGenerated headline:")
    print(result.headline)
    print("\nProvider:")
    print(result.provider)
    print("\nATS keywords:")
    print(", ".join(result.ats_keywords))
    print("\nRecruiter focus:")
    print(result.recruiter_focus)
    print("\nSaved to outputs/generated_headline.json")


if __name__ == "__main__":
    main()
