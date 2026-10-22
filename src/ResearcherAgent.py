
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import SerperDevTool


# ==========================================
# STEP 1: Load environment variables
# ==========================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

if not OPENAI_API_KEY or not SERPER_API_KEY:
    raise ValueError(
        "Missing OPENAI_API_KEY or SERPER_API_KEY in .env"
    )

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["SERPER_API_KEY"] = SERPER_API_KEY

today = datetime.now(
    ZoneInfo("Asia/Kolkata")
).strftime("%Y-%m-%d")


# ==========================================
# STEP 2: Configure LLM and Search Tool
# ==========================================

llm = LLM(
    model="openai/gpt-4o-mini",
    temperature=0.2
)

search_tool = SerperDevTool()


# ==========================================
# STEP 3: Create Researcher Agent
# ==========================================

researcher = Agent(
    role="Senior Technology News Researcher",

    goal=(
        "Find today's top 3 important technology "
        "news stories using reliable sources."
    ),

    backstory=(
        "You are an experienced technology journalist "
        "who researches AI, software, cloud computing, "
        "cybersecurity and emerging technologies. "
        "You verify publication dates and facts."
    ),

    tools=[search_tool],
    llm=llm,
    verbose=True,
    allow_delegation=False
)


# ==========================================
# STEP 4: Create Writer Agent
# ==========================================

writer = Agent(
    role="Professional Tech Newsletter Writer",

    goal=(
        "Convert researched technology news into "
        "a clear, engaging newsletter of exactly "
        "5 lines."
    ),

    backstory=(
        "You are an expert newsletter editor who "
        "writes short, accurate and engaging "
        "technology updates for professionals."
    ),

    tools=[],
    llm=llm,
    verbose=True,
    allow_delegation=False
)


# ==========================================
# STEP 5: Research Task
# ==========================================

research_task = Task(
    description=(
        f"Find the top 3 technology news stories "
        f"for {today}.\n"
        "Use SerperDevTool to search the web.\n"
        "Prioritize AI, software, cloud and "
        "cybersecurity developments.\n"
        "Verify each story's date and source.\n"
        "For each story, provide:\n"
        "1. Headline\n"
        "2. Two-sentence summary\n"
        "3. Source URL\n"
        "4. Publication date\n"
        "If fewer than 3 stories can be verified "
        "for today, clearly state that."
    ),

    expected_output=(
        "Three verified technology stories with "
        "headlines, summaries, dates and URLs, "
        "or a clear indication of any missing "
        "verified stories."
    ),

    agent=researcher
)


# ==========================================
# STEP 6: Newsletter Writing Task
# ==========================================

writing_task = Task(
    description=(
        "Using ONLY the Researcher's output, "
        "write a technology newsletter.\n"
        "Output exactly 5 non-empty lines:\n"
        "Line 1: Tech Daily | Date\n"
        "Line 2: Story 1 with a concise summary\n"
        "Line 3: Story 2 with a concise summary\n"
        "Line 4: Story 3 with a concise summary\n"
        "Line 5: Key takeaway\n"
        "Do not invent missing news stories.\n"
        "If a story is unavailable, state "
        "'No verified story available' on its line.\n"
        "No bullet wrapping, markdown headings, "
        "or extra explanations."
    ),

    expected_output=(
        "Exactly 5 non-empty lines, with no extra "
        "text or blank lines. Line 1 is the title "
        "and date; lines 2-4 contain one technology "
        "story each; line 5 is the key takeaway."
    ),

    agent=writer,

    # Explicitly pass Researcher's task result
    context=[research_task]
)


# ==========================================
# STEP 7: Create Crew
# ==========================================

tech_news_crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    process=Process.sequential,
    verbose=True
)


# ==========================================
# STEP 8: Execute Crew and Save TXT File
# ==========================================

from pathlib import Path

if __name__ == "__main__":

    result = tech_news_crew.kickoff()

    newsletter = str(result.raw).strip()

    lines = [
        line.strip()
        for line in newsletter.splitlines()
        if line.strip()
    ]

    # Validate exactly 5 lines
    if len(lines) != 5:
        raise ValueError(
            f"Expected exactly 5 lines, "
            f"but received {len(lines)}."
        )

    # Generate filename with today's date
    today = datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).strftime("%Y-%m-%d")

    filename = f"Tech_Newsletter_{today}.txt"

    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save newsletter to text file
    file_path = output_dir / filename

    file_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8"
    )

    # Display final output
    print("\n========== FINAL NEWSLETTER ==========")
    print("\n".join(lines))

    print(f"\nNewsletter saved successfully: {file_path}")
