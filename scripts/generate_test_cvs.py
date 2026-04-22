"""Generate 4 test candidate CV PDFs for the Credit Risk Data Scientist role."""
import os, sys
from fpdf import FPDF

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "test_cvs")
os.makedirs(OUT, exist_ok=True)


class CV(FPDF):
    def header(self): pass
    def footer(self): pass

    def name_block(self, name, title, contact):
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(174, 0, 1)
        self.cell(0, 10, name, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(40, 40, 40)
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(110, 110, 110)
        self.multi_cell(0, 5, contact)
        self.set_draw_color(174, 0, 1)
        self.set_line_width(0.5)
        self.line(15, self.get_y() + 2, 195, self.get_y() + 2)
        self.ln(6)

    def section(self, heading):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(174, 0, 1)
        self.cell(0, 7, heading, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.2)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(2)

    def job(self, role, company, period):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(30, 30, 30)
        self.cell(0, 6, role + "  |  " + company + "  (" + period + ")", new_x="LMARGIN", new_y="NEXT")

    def bullet(self, text):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(50, 50, 50)
        self.set_x(20)
        w = self.w - self.r_margin - self.get_x()
        self.multi_cell(w, 5, "*  " + text)
        self.set_x(self.l_margin)

    def body(self, text):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(50, 50, 50)
        self.set_x(self.l_margin)
        w = self.w - self.r_margin - self.get_x()
        self.multi_cell(w, 5, text)
        self.set_x(self.l_margin)

    def skill_row(self, label, value):
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(60, 60, 60)
        self.cell(38, 5, label, new_x="RIGHT", new_y="TOP")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(50, 50, 50)
        w = self.w - self.r_margin - self.get_x()
        self.multi_cell(w, 5, value)
        self.set_x(self.l_margin)

    def gap(self, h=3):
        self.ln(h)


def cv1():
    pdf = CV()
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    pdf.set_top_margin(15)
    pdf.add_page()
    pdf.name_block(
        "Aisha Okonkwo",
        "Senior Data Scientist - Credit Risk & Explainable AI",
        "London, UK  |  aisha.okonkwo@testcandidate.dev  |  +44 7700 100001"
    )
    pdf.section("PROFESSIONAL SUMMARY")
    pdf.body(
        "Senior Data Scientist with 6+ years of experience in fintech and credit risk modelling. "
        "Specialist in explainable AI (SHAP, LIME) with deep expertise in Linear Regression, "
        "Logistic Regression, XGBoost, and NLP-based entity resolution. Proven track record "
        "deploying high-scale models on AWS for affordability scoring and fraud detection at "
        "ClearScore and Experian."
    )
    pdf.gap()
    pdf.section("EXPERIENCE")
    pdf.job("Senior Data Scientist", "ClearScore, London", "2021 - Present")
    pdf.bullet("Built affordability and income estimation models using Linear Regression and XGBoost, reducing loan default rates by 18%.")
    pdf.bullet("Developed entity resolution pipeline with fuzzy matching and named entity recognition (NER) to deduplicate 50M+ consumer records.")
    pdf.bullet("Implemented SHAP-based explainability framework ensuring full FCA regulatory compliance.")
    pdf.bullet("Deployed models to AWS SageMaker using Docker, Kubernetes, and CI/CD pipelines via GitHub Actions.")
    pdf.bullet("Used LLM APIs (GPT-4) for context engineering on unstructured transaction data.")
    pdf.gap()
    pdf.job("Data Scientist", "Experian, Nottingham", "2019 - 2021")
    pdf.bullet("Designed credit risk scoring models combining Logistic Regression and XGBoost gradient boosting.")
    pdf.bullet("Built data pipelines using SQL, Apache Spark, Pandas, and NumPy.")
    pdf.bullet("Conducted behavioural signal analysis: spending volatility, income stability, fraud risk patterns.")
    pdf.bullet("Applied NLP for transaction categorisation and merchant entity matching at scale.")
    pdf.gap()
    pdf.job("Junior Data Scientist", "Lloyds Banking Group", "2018 - 2019")
    pdf.bullet("Fraud detection model development using machine learning and statistical data analysis.")
    pdf.bullet("SQL-based feature engineering on large transactional PostgreSQL datasets.")
    pdf.gap()
    pdf.section("EDUCATION")
    pdf.body("MSc Data Science  -  University College London (UCL), 2018")
    pdf.body("BSc Mathematics & Statistics  -  University of Warwick, 2017")
    pdf.gap()
    pdf.section("TECHNICAL SKILLS")
    pdf.skill_row("Python:", "Pandas, NumPy, Scikit-Learn, XGBoost, LightGBM (expert level)")
    pdf.skill_row("ML Models:", "Linear Regression, Logistic Regression, Gradient Boosting, Random Forest")
    pdf.skill_row("Explainability:", "SHAP, LIME - regulatory model explanations for FCA compliance")
    pdf.skill_row("NLP:", "Entity resolution, fuzzy matching, NER, spaCy, record linkage")
    pdf.skill_row("GenAI:", "LLM APIs, prompt engineering, context engineering, RAG pipelines")
    pdf.skill_row("Cloud:", "AWS (SageMaker, S3, Lambda), Docker, Kubernetes, CI/CD, Git")
    pdf.skill_row("Data:", "SQL, PostgreSQL, Apache Spark, Kafka")
    pdf.gap()
    pdf.section("CERTIFICATIONS")
    pdf.body("AWS Certified Machine Learning Specialty")
    pdf.body("Databricks Certified Associate Developer for Apache Spark")
    path = os.path.join(OUT, "aisha_okonkwo_cv.pdf")
    pdf.output(path)
    print("  Saved: " + path)


def cv2():
    pdf = CV()
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    pdf.set_top_margin(15)
    pdf.add_page()
    pdf.name_block(
        "James Chen",
        "Data Scientist - E-Commerce & Retail Analytics",
        "Manchester, UK  |  james.chen@testcandidate.dev  |  +44 7700 100002"
    )
    pdf.section("PROFESSIONAL SUMMARY")
    pdf.body(
        "Data Scientist with 4 years of experience building recommendation systems and customer "
        "segmentation models in e-commerce. Proficient in Python, machine learning, and data analysis. "
        "Strong SQL and data engineering skills. No prior fintech or credit risk background, "
        "but eager to transition into financial services."
    )
    pdf.gap()
    pdf.section("EXPERIENCE")
    pdf.job("Data Scientist", "ASOS, Manchester", "2021 - Present")
    pdf.bullet("Customer churn prediction models using Logistic Regression and Random Forest (scikit-learn).")
    pdf.bullet("Product recommendation engine using collaborative filtering and deep learning (PyTorch).")
    pdf.bullet("Spending pattern and behavioural cluster analysis using Pandas and NumPy.")
    pdf.bullet("A/B test analysis and statistical significance testing.")
    pdf.bullet("No SHAP or formal explainability framework used in production.")
    pdf.gap()
    pdf.job("Junior Data Analyst", "Booking.com", "2020 - 2021")
    pdf.bullet("SQL-based reporting and data pipeline development (PostgreSQL, Python).")
    pdf.bullet("Exploratory data analysis and visualisation for marketing campaigns.")
    pdf.bullet("Machine learning models for price optimisation.")
    pdf.gap()
    pdf.section("EDUCATION")
    pdf.body("BSc Computer Science  -  University of Manchester, 2020")
    pdf.gap()
    pdf.section("TECHNICAL SKILLS")
    pdf.skill_row("Python:", "Pandas, NumPy, Scikit-Learn, PyTorch, TensorFlow")
    pdf.skill_row("ML Models:", "Logistic Regression, Random Forest, basic Gradient Boosting")
    pdf.skill_row("NLP:", "Basic text classification, sentiment analysis (no entity resolution)")
    pdf.skill_row("Data:", "SQL, PostgreSQL, MongoDB, basic AWS (EC2, S3), Docker")
    pdf.skill_row("Practices:", "Git, Agile, Scrum")
    pdf.gap()
    pdf.section("SKILL GAPS FOR THIS ROLE")
    pdf.body("No SHAP or explainability frameworks | No XGBoost in production | No entity resolution")
    pdf.body("No credit risk or fintech industry experience | No affordability or fraud modelling")
    path = os.path.join(OUT, "james_chen_cv.pdf")
    pdf.output(path)
    print("  Saved: " + path)


def cv3():
    pdf = CV()
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    pdf.set_top_margin(15)
    pdf.add_page()
    pdf.name_block(
        "Priya Sharma",
        "ML Engineer - Deep Learning & Generative AI",
        "Edinburgh, UK  |  priya.sharma@testcandidate.dev  |  +44 7700 100003"
    )
    pdf.section("PROFESSIONAL SUMMARY")
    pdf.body(
        "ML Engineer with 2.5 years of experience deploying deep learning and generative AI models. "
        "Specialist in LLM APIs, prompt engineering, and computer vision. Strong Python engineering "
        "skills. Background is primarily in neural networks and unstructured data rather than "
        "classical statistics, credit risk, or entity resolution."
    )
    pdf.gap()
    pdf.section("EXPERIENCE")
    pdf.job("ML Engineer", "Skyscanner, Edinburgh", "2022 - Present")
    pdf.bullet("Computer vision models using PyTorch and TensorFlow for image recognition at scale.")
    pdf.bullet("Integrated LLM APIs (OpenAI, Anthropic Claude) for customer-facing GenAI features.")
    pdf.bullet("Prompt engineering and context engineering for RAG pipelines.")
    pdf.bullet("Containerised models with Docker; deployed on AWS with CI/CD automation.")
    pdf.gap()
    pdf.job("Graduate ML Engineer", "FanDuel, Edinburgh", "2021 - 2022")
    pdf.bullet("Recommendation models using deep learning and collaborative filtering.")
    pdf.bullet("Python data pipelines with Pandas and NumPy.")
    pdf.bullet("NLP work: text classification and sentiment analysis using Hugging Face transformers.")
    pdf.gap()
    pdf.section("EDUCATION")
    pdf.body("MSc Artificial Intelligence  -  University of Edinburgh, 2021")
    pdf.body("BSc Computer Science  -  Heriot-Watt University, 2020")
    pdf.gap()
    pdf.section("TECHNICAL SKILLS")
    pdf.skill_row("Python:", "Pandas, NumPy, PyTorch, TensorFlow, Hugging Face Transformers")
    pdf.skill_row("Deep Learning:", "CNNs, Transformers, LLMs, diffusion models")
    pdf.skill_row("GenAI:", "LLM APIs, prompt engineering, context engineering, RAG pipelines")
    pdf.skill_row("NLP:", "Text classification, transformers (no entity resolution or fuzzy matching)")
    pdf.skill_row("Cloud:", "AWS, Docker, Kubernetes, CI/CD, Git, Agile")
    pdf.gap()
    pdf.section("SKILL GAPS FOR THIS ROLE")
    pdf.body("No SHAP | No XGBoost | No Linear or Logistic Regression in production")
    pdf.body("No entity resolution or fuzzy matching | No credit risk, fraud, or affordability experience")
    pdf.body("No fintech or financial services background | SQL skills minimal")
    path = os.path.join(OUT, "priya_sharma_cv.pdf")
    pdf.output(path)
    print("  Saved: " + path)


def cv4():
    pdf = CV()
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    pdf.set_top_margin(15)
    pdf.add_page()
    pdf.name_block(
        "Tom Williams",
        "Junior Software Developer",
        "Bristol, UK  |  tom.williams@testcandidate.dev  |  +44 7700 100004"
    )
    pdf.section("PROFESSIONAL SUMMARY")
    pdf.body(
        "Junior Software Developer with 1 year of professional experience in web application "
        "development. BSc Mathematics graduate with a strong theoretical background in statistics "
        "and linear algebra. Enthusiastic about data science and machine learning. Currently "
        "completing online courses in Python and data analysis. No professional ML or fintech experience."
    )
    pdf.gap()
    pdf.section("EXPERIENCE")
    pdf.job("Junior Software Developer", "Local Web Agency, Bristol", "2024 - Present")
    pdf.bullet("Built web applications using JavaScript, React, and Node.js.")
    pdf.bullet("Basic Python scripting for data export and automation tasks.")
    pdf.bullet("SQL queries for database reporting (MySQL).")
    pdf.bullet("Agile/Scrum team using Git version control.")
    pdf.gap()
    pdf.section("EDUCATION")
    pdf.body("BSc Mathematics  -  University of Bristol, 2023")
    pdf.body("Modules: Linear Algebra, Statistics, Probability Theory, Calculus, Numerical Methods")
    pdf.body("Final Year Project: Statistical analysis of financial time series (R)")
    pdf.gap()
    pdf.section("TECHNICAL SKILLS")
    pdf.skill_row("Programming:", "Python (beginner), JavaScript, React, Node.js, SQL (basic MySQL)")
    pdf.skill_row("Statistics:", "Linear models and probability - academic only, no professional use")
    pdf.skill_row("ML:", "Completed Andrew Ng Coursera ML course - zero professional deployment")
    pdf.skill_row("Tools:", "Git, basic Docker, Agile, Scrum, Excel, R (academic)")
    pdf.gap()
    pdf.section("SKILL GAPS FOR THIS ROLE")
    pdf.body("No professional data science or machine learning experience")
    pdf.body("No SHAP, XGBoost, Scikit-Learn, Pandas or NumPy at professional level")
    pdf.body("No NLP, entity resolution, or fraud/credit risk work")
    pdf.body("No AWS or cloud deployment experience | No fintech background")
    pdf.body("Only 1 year of total professional experience (role requires 2+ years in fintech)")
    path = os.path.join(OUT, "tom_williams_cv.pdf")
    pdf.output(path)
    print("  Saved: " + path)


cv1()
cv2()
cv3()
cv4()
print("\nAll 4 CVs saved to data/test_cvs/")
