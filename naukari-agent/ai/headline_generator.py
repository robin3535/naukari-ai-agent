import json
import os
import re
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from pathlib import Path

import requests
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app_logging.logger_config import setup_logger


logger = setup_logger()


@dataclass
class HeadlineInputs:
    resume_text: str
    tech_stack: str
    experience: str
    target_role: str


@dataclass
class GeneratedHeadline:
    headline: str
    ats_keywords: list[str]
    recruiter_focus: str
    provider: str


class HeadlineAgent(ABC):
    """
    Provider-specific headline generator.
    """

    name: str

    @abstractmethod
    def is_configured(self) -> bool:
        pass

    @abstractmethod
    def generate(
        self,
        inputs: HeadlineInputs
    ) -> GeneratedHeadline:
        pass


class HeadlineResponseParser:
    def parse(
        self,
        raw_response: str,
        provider: str
    ) -> GeneratedHeadline:
        cleaned = raw_response.strip()

        if cleaned.startswith("```"):
            match = re.search(
                r"```(?:json)?\s*(.*?)\s*```",
                cleaned,
                re.DOTALL | re.IGNORECASE
            )
            if match:
                cleaned = match.group(1).strip()

        payload = json.loads(cleaned)

        headline = str(payload["headline"]).strip()
        if not headline.endswith((".", "!", "?")):
            headline = f"{headline}."

        keywords = payload.get("ats_keywords", [])
        if not isinstance(keywords, list):
            keywords = []

        return GeneratedHeadline(
            headline=headline,
            ats_keywords=[
                str(keyword).strip()
                for keyword in keywords
                if str(keyword).strip()
            ],
            recruiter_focus=str(payload.get("recruiter_focus", "")).strip(),
            provider=provider
        )


def build_prompt_text(
    inputs: HeadlineInputs
) -> str:
    return (
        "You are an expert Indian job-market resume optimizer. "
        "Create concise, recruiter-focused Naukri profile headlines. "
        "Prefer ATS-friendly keywords, measurable experience, target role alignment, "
        "and natural wording.\n\n"
        f"Resume text:\n{inputs.resume_text}\n\n"
        f"Tech stack:\n{inputs.tech_stack}\n\n"
        f"Experience:\n{inputs.experience}\n\n"
        f"Target role:\n{inputs.target_role}\n\n"
        "Return only valid JSON with this exact shape:\n"
        "{\n"
        '  "headline": "single optimized Naukri headline, 180-240 characters, ending with punctuation",\n'
        '  "ats_keywords": ["keyword 1", "keyword 2", "keyword 3"],\n'
        '  "recruiter_focus": "one short sentence explaining the positioning"\n'
        "}"
    )


class OpenAIHeadlineAgent(HeadlineAgent):
    name = "openai"

    def __init__(
        self,
        parser: HeadlineResponseParser
    ) -> None:
        self.parser = parser
        self.model = os.getenv("OPENAI_MODEL", "gpt-5-mini")

    def is_configured(self) -> bool:
        return bool(os.getenv("OPENAI_API_KEY"))

    def generate(
        self,
        inputs: HeadlineInputs
    ) -> GeneratedHeadline:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "You are an expert Indian job-market resume optimizer. "
                        "Return only valid JSON."
                    ),
                ),
                ("human", "{prompt_text}"),
            ]
        )

        chain = prompt | ChatOpenAI(model=self.model) | StrOutputParser()

        logger.info(f"Generating headline with OpenAI model: {self.model}")
        raw_response = chain.invoke(
            {
                "prompt_text": build_prompt_text(inputs)
            }
        )

        return self.parser.parse(
            raw_response=raw_response,
            provider=self.name
        )


class GeminiHeadlineAgent(HeadlineAgent):
    name = "gemini"

    API_URL_TEMPLATE = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "{model}:generateContent"
    )

    def __init__(
        self,
        parser: HeadlineResponseParser
    ) -> None:
        self.parser = parser
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    def is_configured(self) -> bool:
        return bool(os.getenv("GEMINI_API_KEY"))

    def generate(
        self,
        inputs: HeadlineInputs
    ) -> GeneratedHeadline:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set")

        logger.info(f"Generating headline with Gemini model: {self.model}")

        response = requests.post(
            self.API_URL_TEMPLATE.format(model=self.model),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key
            },
            json={
                "contents": [
                    {
                        "parts": [
                            {
                                "text": build_prompt_text(inputs)
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "temperature": 0.4
                }
            },
            timeout=45
        )

        response.raise_for_status()

        payload = response.json()
        raw_response = payload["candidates"][0]["content"]["parts"][0]["text"]

        return self.parser.parse(
            raw_response=raw_response,
            provider=self.name
        )


class EnvFallbackHeadlineAgent(HeadlineAgent):
    name = "env_fallback"

    def is_configured(self) -> bool:
        return bool(os.getenv("NAUKRI_HEADLINE", "").strip())

    def generate(
        self,
        inputs: HeadlineInputs
    ) -> GeneratedHeadline:
        headline = os.getenv("NAUKRI_HEADLINE", "").strip()
        if not headline:
            raise ValueError("NAUKRI_HEADLINE is not set")

        if not headline.endswith((".", "!", "?")):
            headline = f"{headline}."

        return GeneratedHeadline(
            headline=headline,
            ats_keywords=[
                keyword.strip()
                for keyword in inputs.tech_stack.split(",")
                if keyword.strip()
            ],
            recruiter_focus="Fallback headline from local .env.",
            provider=self.name
        )


class MultiAgentHeadlineGenerator:
    """
    Tries headline agents in order until one succeeds.
    """

    OUTPUT_PATH = Path("outputs/generated_headline.json")

    def __init__(
        self,
        agents: list[HeadlineAgent] | None = None
    ) -> None:
        parser = HeadlineResponseParser()
        self.agents = agents or [
            OpenAIHeadlineAgent(parser),
            GeminiHeadlineAgent(parser),
            EnvFallbackHeadlineAgent(),
        ]

    def generate(
        self,
        inputs: HeadlineInputs
    ) -> GeneratedHeadline:
        self.validate_inputs(inputs)

        errors: list[str] = []

        for agent in self.agents:
            if not agent.is_configured():
                logger.info(f"Skipping {agent.name}; not configured")
                continue

            try:
                result = agent.generate(inputs)
                self.save(result)
                logger.info(f"Generated headline via {result.provider}: {result.headline}")
                logger.info(f"ATS keywords: {', '.join(result.ats_keywords)}")
                logger.info(f"Recruiter focus: {result.recruiter_focus}")
                return result
            except Exception as error:
                message = f"{agent.name} failed: {error}"
                logger.error(message)
                errors.append(message)

        raise RuntimeError(
            "All headline agents failed. "
            + " | ".join(errors)
        )

    def validate_inputs(
        self,
        inputs: HeadlineInputs
    ) -> None:
        missing_fields = [
            field_name
            for field_name, value in asdict(inputs).items()
            if not value
        ]

        if missing_fields:
            raise ValueError(
                "Missing headline inputs: "
                + ", ".join(missing_fields)
            )

    def save(
        self,
        result: GeneratedHeadline
    ) -> None:
        self.OUTPUT_PATH.parent.mkdir(exist_ok=True)
        self.OUTPUT_PATH.write_text(
            json.dumps(asdict(result), indent=2),
            encoding="utf-8"
        )


class ResumeHeadlineGenerator(MultiAgentHeadlineGenerator):
    """
    Backward-compatible name for the multi-agent generator.
    """


def load_headline_inputs_from_env() -> HeadlineInputs | None:
    resume_text = os.getenv("RESUME_TEXT", "").strip()
    resume_text_path = os.getenv("RESUME_TEXT_PATH", "resume.txt").strip()

    if not resume_text and resume_text_path:
        resume_path = Path(resume_text_path)
        if not resume_path.exists():
            logger.info(
                f"Skipping AI headline generation; resume file not found: {resume_text_path}"
            )
            return None

        resume_text = resume_path.read_text(
            encoding="utf-8"
        ).strip()

    inputs = HeadlineInputs(
        resume_text=resume_text,
        tech_stack=os.getenv(
            "TECH_STACK",
            ".NET, React, Vue.js, REST API, GraphQL, SQL, AI integrations"
        ).strip(),
        experience=os.getenv("EXPERIENCE", "3.5+ years").strip(),
        target_role=os.getenv("TARGET_ROLE", "Full Stack Developer").strip()
    )

    missing_fields = [
        field_name
        for field_name, value in asdict(inputs).items()
        if not value
    ]

    if missing_fields:
        logger.info(
            "Skipping AI headline generation; missing inputs: "
            + ", ".join(missing_fields)
        )
        return None

    return inputs


def generate_headline_from_env() -> str | None:
    inputs = load_headline_inputs_from_env()
    if not inputs:
        return None

    try:
        generator = MultiAgentHeadlineGenerator()
        result = generator.generate(inputs)
        return result.headline
    except Exception as error:
        logger.exception(f"AI headline generation failed: {error}")
        return None
