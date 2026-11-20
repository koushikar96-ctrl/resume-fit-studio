import re
from typing import Any


def default_resume() -> dict[str, Any]:
    return {
        "personal": {
            "name": "",
            "email": "",
            "phone": "",
            "location": "",
            "portfolio": "",
        },
        "summary": "",
        "experience": [
            {
                "role": "",
                "company": "",
                "location": "",
                "start_date": "",
                "end_date": "",
                "description": "",
            }
        ],
        "projects": [
            {
                "name": "",
                "description": "",
                "technologies": [],
                "link": "",
            }
        ],
        "education": [
            {
                "school": "",
                "degree": "",
                "field": "",
                "start_date": "",
                "end_date": "",
            }
        ],
        "skills": ["Python", "SQL"],
        "certifications": [],
        "achievements": [],
        "custom_sections": [],
    }


STOP_WORDS = {
    # Common English Stop Words
    "a", "about", "above", "across", "after", "afterwards", "again", "against", "all", "almost", "alone", "along",
    "already", "also", "although", "always", "am", "among", "amongst", "an", "and", "another", "any", "anyhow",
    "anyone", "anything", "anyway", "anywhere", "are", "around", "as", "at", "be", "became", "because", "become",
    "becomes", "becoming", "been", "before", "beforehand", "behind", "being", "below", "beside", "besides", "between",
    "beyond", "both", "but", "by", "can", "cannot", "could", "did", "do", "does", "doing", "done", "down", "due",
    "during", "each", "eg", "either", "else", "elsewhere", "enough", "etc", "even", "ever", "every", "everyone",
    "everything", "everywhere", "except", "for", "former", "formerly", "from", "further", "had", "has", "have", "he",
    "hence", "her", "here", "hereafter", "hereby", "herein", "hereupon", "hers", "herself", "him", "himself", "his",
    "how", "however", "i", "ie", "if", "in", "inc", "indeed", "into", "is", "it", "its", "itself", "just", "latter",
    "latterly", "least", "less", "ltd", "made", "many", "may", "me", "meanwhile", "might", "more", "moreover", "most",
    "mostly", "much", "must", "my", "myself", "namely", "neither", "never", "nevertheless", "next", "no", "nobody",
    "none", "noone", "nor", "not", "nothing", "now", "nowhere", "of", "off", "often", "on", "once", "one", "only",
    "onto", "or", "other", "others", "otherwise", "our", "ours", "ourselves", "out", "over", "own", "part", "per",
    "perhaps", "please", "put", "rather", "same", "see", "seem", "seemed", "seeming", "seems", "several", "she",
    "should", "since", "so", "some", "somehow", "someone", "something", "sometime", "sometimes", "somewhere", "still",
    "such", "take", "than", "that", "the", "their", "them", "themselves", "then", "thence", "there", "thereafter",
    "thereby", "therefore", "therein", "thereupon", "these", "they", "this", "those", "though", "through", "throughout",
    "thru", "thus", "to", "together", "too", "toward", "towards", "under", "until", "up", "upon", "us", "very",
    "via", "was", "we", "well", "were", "what", "whatever", "when", "whence", "whenever", "where", "whereafter",
    "whereas", "whereby", "wherein", "whereupon", "wherever", "whether", "which", "while", "whither", "who", "whoever",
    "whole", "whom", "whose", "why", "will", "with", "within", "without", "would", "yet", "you", "your", "yours",
    "yourself", "yourselves",
    # Job Ad Filler & Meta Words
    "role", "overview", "title", "job", "seeking", "responsibilities", "requirements", "skills", "experience", "degree",
    "equivalent", "practical", "preferred", "highly", "closely", "stay", "up-to-date", "latest", "new", "work",
    "working", "help", "make", "using", "use", "used", "user", "users", "team", "teams", "strong", "good", "great",
    "excellent", "ability", "candidate", "candidates", "joining", "company", "industry", "opportunity", "key", "must",
    "should", "will", "are", "between", "bridge", "collaborate", "complex", "continuous", "deploy", "deploying",
    "developers", "evaluating", "existing", "familiarity", "field", "ingest", "innovation", "integrate", "maintain",
    "methodologies", "mindset", "overviewwe", "preprocess", "product", "production", "proficiency", "related", "resource",
    "robust", "skilled", "solve", "speed", "structured", "test", "this", "tools", "train", "transforming", "engineer",
    "developer", "senior", "junior", "lead", "staff", "principal", "manager", "specialist", "intern", "advancements",
    "automated", "bachelor", "bachelors", "master", "masters", "business", "capabilities", "clean", "design", "build",
    "systems", "system", "communication", "problem-solving", "data-driven", "environment", "environments", "technologies",
    "technology", "methodology", "research", "science", "solutions", "services", "management",
}


def normalize_keyword(token: str) -> str:
    cleaned = re.sub(r"[^a-z0-9+.#-]", "", token.lower())
    return cleaned.strip(".-+")


def clean_job_or_resume_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"(?<=[a-zA-Z])\.(?=[a-zA-Z])", " ", text)
    text = re.sub(r"(?<=[a-zA-Z]):(?=[a-zA-Z])", " ", text)
    text = re.sub(r"(?<!ci)(?<!ai)(?<!ml)/(?![cCdD])", " ", text)
    return text


def extract_keyword_set(text: str) -> set[str]:
    if not text:
        return set()

    cleaned_text = clean_job_or_resume_text(text)
    tokens = re.findall(r"[a-zA-Z0-9+.#-]+", cleaned_text.lower())
    keywords = set()
    for token in tokens:
        keyword = normalize_keyword(token)
        if keyword and len(keyword) > 1 and keyword not in STOP_WORDS and not keyword.isdigit():
            keywords.add(keyword)
    return keywords
