"""
Plain-English filler text for synthetic data generation.

Faker's .paragraph()/.sentence()/.text() always produce Latin lorem-ipsum
regardless of locale -- the "lorem" provider isn't localized. Use these
helpers instead anywhere synthetic job/candidate text needs to look like
real (English) prose.

Two separate pools are kept because job postings and candidate resumes read
very differently: job text speaks about the role/team from the employer's
side, candidate text speaks about the person's own track record.
"""
import random

_JOB_SENTENCES = [
    "We are looking for someone who thrives in a fast-paced, collaborative environment.",
    "This role offers the opportunity to work on high-impact projects from day one.",
    "Strong communication and problem-solving skills are essential for success here.",
    "The successful candidate will work closely with cross-functional teams to deliver results.",
    "We value curiosity, ownership, and a willingness to learn new tools and technologies.",
    "You will be expected to balance competing priorities while maintaining high standards of quality.",
    "This position reports directly to the department lead and works closely with senior stakeholders.",
    "We're building a diverse, inclusive team that reflects the communities we serve.",
    "The ideal candidate is comfortable working independently as well as part of a larger team.",
    "You will have the opportunity to mentor junior colleagues and share best practices.",
    "We offer a flexible working environment with opportunities for professional growth.",
    "Attention to detail and a methodical approach to problem-solving are key for this role.",
    "This is a great opportunity to make a meaningful impact within a growing organisation.",
    "The team values open feedback, continuous improvement, and honest communication.",
    "Candidates should be comfortable presenting findings to both technical and non-technical audiences.",
    "We are committed to investing in the ongoing development of every team member.",
    "This role requires a pragmatic, results-driven approach to solving complex problems.",
    "You will collaborate with stakeholders across the business to define priorities and requirements.",
    "The company has a strong track record of promoting from within.",
    "We're looking for someone who can balance strategic thinking with hands-on execution.",
    "Adaptability and resilience are important qualities for succeeding in this fast-moving industry.",
    "You will play a key role in shaping the direction of upcoming projects.",
    "The team meets regularly to review progress, share learnings, and plan next steps.",
    "We encourage experimentation and are not afraid to learn from mistakes.",
    "This position offers exposure to a wide variety of projects and stakeholders.",
    "Excellent organisational skills and the ability to manage multiple deadlines are required.",
    "You will be joining a supportive team that values collaboration over competition.",
    "The company places a strong emphasis on data-driven decision making.",
    "We're looking for a proactive self-starter who can identify opportunities for improvement.",
    "This role would suit someone who enjoys tackling ambiguous, open-ended problems.",
    "Prior experience working in a similarly regulated or fast-paced environment is a plus.",
    "You will be given the autonomy to make decisions and take ownership of outcomes.",
    "We are looking to grow the team significantly over the next twelve months.",
    "The role involves regular collaboration with teams based in multiple time zones.",
    "A genuine passion for the industry and a willingness to keep learning are highly valued.",
    "You will help define processes and best practices as the team continues to scale.",
    "This is a hybrid role with the flexibility to work from home several days a week.",
    "We're proud of our collaborative culture and our focus on continuous learning.",
    "The successful candidate will bring both technical depth and strong interpersonal skills.",
    "This role offers a competitive package alongside a strong focus on work-life balance.",
]

_CANDIDATE_SENTENCES = [
    "Led a cross-functional team to deliver a major project ahead of schedule.",
    "Reduced operational costs by streamlining workflows and automating routine tasks.",
    "Collaborated closely with product and design teams to translate requirements into working solutions.",
    "Mentored junior team members and contributed to onboarding documentation.",
    "Consistently exceeded quarterly targets by identifying process inefficiencies and proposing data-driven fixes.",
    "Presented findings to senior stakeholders, translating complex analysis into actionable recommendations.",
    "Played a key role in migrating legacy systems to a modern, scalable architecture.",
    "Built strong working relationships with clients and internal teams across multiple regions.",
    "Introduced new practices that significantly reduced errors and rework.",
    "Regularly contributed to peer reviews and helped establish team best practices.",
    "Managed competing priorities across several concurrent projects without missing deadlines.",
    "Recognised by management for consistently delivering high-quality work under tight timelines.",
    "Took ownership of end-to-end delivery, from initial planning through to launch.",
    "Worked closely with cross-functional teams to ensure decisions were grounded in reliable data.",
    "Adapted quickly to new tools and processes as project requirements evolved.",
    "Actively participated in hiring and onboarding, helping to grow the wider team.",
    "Balanced hands-on execution with broader planning and strategy responsibilities.",
    "Received positive feedback from stakeholders for clear communication and reliable delivery.",
    "Championed process improvements that measurably increased team productivity.",
    "Regularly collaborated with colleagues across different time zones to align on priorities.",
    "Developed a strong reputation for solving difficult problems under pressure.",
    "Took the initiative to identify gaps in existing processes and proposed practical solutions.",
    "Worked directly with leadership to define goals and track progress against them.",
    "Known among peers for clear documentation and a methodical approach to problem-solving.",
    "Volunteered to lead internal training sessions on tools and best practices.",
    "Successfully delivered projects in a fast-paced environment with frequently shifting priorities.",
    "Built and maintained strong relationships with stakeholders across the business.",
    "Consistently sought out feedback and used it to improve both process and output.",
    "Played an active role in shaping team culture and improving collaboration.",
    "Recognised for reliability, attention to detail, and consistently meeting commitments.",
    "Comfortable working independently with minimal supervision on ambiguous problems.",
    "Brought a pragmatic, results-oriented approach to every project undertaken.",
    "Regularly sought opportunities to learn new skills and stay current with industry trends.",
    "Worked effectively across disciplines, bridging gaps between technical and non-technical teams.",
    "Took ownership of onboarding new team members and improving internal documentation.",
    "Demonstrated strong judgement when prioritising work under resource constraints.",
    "Contributed ideas that were adopted more broadly across the wider organisation.",
    "Built a track record of dependable delivery across a range of project types.",
    "Known for asking the right questions early to avoid costly rework later.",
    "Proactively flagged risks and worked with the team to resolve them before they escalated.",
]


def _pick(pool: list[str], n: int) -> list[str]:
    if n <= len(pool):
        return random.sample(pool, n)
    return random.choices(pool, k=n)


def job_sentences(n: int) -> list[str]:
    return _pick(_JOB_SENTENCES, n)


def job_paragraph(nb_sentences: int = 3) -> str:
    return " ".join(job_sentences(nb_sentences))


def candidate_sentences(n: int) -> list[str]:
    return _pick(_CANDIDATE_SENTENCES, n)


def candidate_paragraph(nb_sentences: int = 3) -> str:
    return " ".join(candidate_sentences(nb_sentences))
