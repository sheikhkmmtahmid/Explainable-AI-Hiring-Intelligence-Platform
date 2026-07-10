import { Link } from 'react-router-dom'
import { ArrowLeft, ExternalLink, Mail } from 'lucide-react'
import LogoIcon from '../components/LogoIcon'

const DATASETS = [
  {
    name: 'EMSCAD (Employment Scam Aegean Dataset)',
    what: 'Real job postings',
    used: '15,546 postings (866 fraudulent flagged rows excluded, plus 1,468 duplicate listings from the same recurring postings)',
    href: 'https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction',
    license: 'CC0 1.0 (Public Domain)',
    licenseHref: 'https://creativecommons.org/publicdomain/zero/1.0/',
  },
  {
    name: 'jobs.am (Armenian CareerCenter postings, 2004 to 2015)',
    what: 'Real job postings',
    used: '17,718 postings (1,283 duplicate listings excluded)',
    href: 'https://www.kaggle.com/datasets/madhab/jobposts',
    license: 'Not stated on Kaggle\'s page at the time I checked',
    licenseHref: null,
  },
  {
    name: 'LinkedIn Job Postings (2023 to 2024)',
    what: 'Real job postings',
    used: '1,949 postings (capped at 2,000, some skipped as duplicates, see note below)',
    href: 'https://www.kaggle.com/datasets/arshkon/linkedin-job-postings',
    license: 'CC BY-SA 4.0',
    licenseHref: 'https://creativecommons.org/licenses/by-sa/4.0/',
  },
  {
    name: 'Djinni Recruitment Dataset (job descriptions + candidate profiles)',
    what: 'Real job postings and anonymized real candidate CVs',
    used: '2,000 job postings + 2,000 candidate profiles (capped)',
    href: 'https://huggingface.co/collections/lang-uk/djinni-recruitment-dataset',
    license: 'MIT',
    licenseHref: 'https://opensource.org/license/mit/',
  },
  {
    name: 'Resume Dataset (livecareer.com sample resumes)',
    what: 'Real (template/example) resumes',
    used: '2,481 resumes (the full dataset; 3 skipped for empty text)',
    href: 'https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset',
    license: 'CC0 1.0 (Public Domain)',
    licenseHref: 'https://creativecommons.org/publicdomain/zero/1.0/',
  },
  {
    name: 'resume_corpus (academic multi-label resume corpus)',
    what: 'Real resumes',
    used: '2,000 resumes (capped, deduplicated)',
    href: 'https://github.com/florex/resume_corpus',
    license: 'CC0 1.0 (Public Domain)',
    licenseHref: 'https://creativecommons.org/publicdomain/zero/1.0/',
  },
  {
    name: 'Resume-Classification-Dataset',
    what: 'Real resumes',
    used: '1,821 resumes (capped at 2,000; some skipped as duplicates)',
    href: 'https://github.com/noran-mohamed/Resume-Classification-Dataset',
    license: 'MIT (repository code)',
    licenseHref: 'https://opensource.org/license/mit/',
  },
  {
    name: 'Resume-Callback Audit Study (Bertrand & Mullainathan, 2004)',
    what: 'Real job postings, fictional audit-study resumes, and real employer callback decisions',
    used: '1,323 job postings, 4,870 resumes, 4,870 real application outcomes (392 real callbacks)',
    href: 'https://www.openintro.org/data/index.php?data=resume',
    license: 'CC BY-SA 3.0',
    licenseHref: 'https://www.openintro.org/license/',
  },
]

export default function About() {
  return (
    <div className="min-h-screen bg-surface-900 text-white">
      <div className="max-w-3xl mx-auto px-6 py-12">
        <Link to="/" className="inline-flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors mb-8">
          <ArrowLeft className="w-4 h-4" /> Back to the app
        </Link>

        <div className="flex items-center gap-3 mb-8">
          <LogoIcon size={40} />
          <div>
            <h1 className="page-title">About HiringAI</h1>
            <p className="text-sm text-gray-500">Written by the person who built it. No marketing copy, just what's actually true.</p>
          </div>
        </div>

        {/* What this is */}
        <section className="space-y-4 mb-12">
          <h2 className="section-title">What I actually built this to do</h2>
          <p className="text-gray-300 leading-relaxed">
            I didn't set out to build another applicant tracking system. There are plenty of those. What I wanted to build
            is a platform that helps a company answer a much harder question: <em>when we chose who to shortlist, interview,
            and hire, were we fair about it?</em> That's a different question than "did our AI rank people well," which is
            much easier and much less useful to answer. I mean: across gender, ethnicity, age range, and disability status,
            did our actual hiring decisions treat comparable candidates comparably?
          </p>
          <p className="text-gray-300 leading-relaxed">
            That's why the fairness audit in this platform is built to run on real hiring decisions: shortlisted,
            interviewed, offered, hired, or rejected, not just on how the AI ranked people. If a company hasn't made any
            real decisions yet, the fairness report says so plainly and falls back to an AI-rank estimate, clearly labeled
            as provisional. I never wanted a report that quietly mixes the two.
          </p>
          <p className="text-gray-300 leading-relaxed">
            What this platform is <strong>not</strong>: it is not a black-box "AI hiring score" that tells you who to hire.
            Every match score comes with an explanation (via SHAP and LIME) showing exactly which factors moved the number
            up or down. It's also not a finished, audited, enterprise-certified product. It's a working demonstration of
            how I'd approach this problem, built end to end by one person.
          </p>
        </section>

        {/* Models */}
        <section className="space-y-5 mb-12">
          <h2 className="section-title">The models doing the actual work</h2>
          <p className="text-gray-300 leading-relaxed">
            Four different pieces of machine learning do four different jobs here. I think it's worth being specific
            about which one does what, because "AI" isn't one thing.
          </p>

          <div className="space-y-4">
            <div className="card p-5">
              <h3 className="font-semibold text-white mb-1">SBERT (Sentence-BERT)</h3>
              <p className="text-sm text-gray-400 mb-2">Compares the <em>meaning</em> of two pieces of text, not just their words.</p>
              <p className="text-sm text-gray-300 mb-3">
                Example: a resume that says "built REST APIs with Django" and a job that asks for "backend web service
                development experience" share almost no exact words, but SBERT recognizes they mean nearly the same
                thing. This is what powers the semantic-similarity part of every match score.
              </p>
              <p className="text-sm text-gray-500 border-t border-surface-500 pt-3">
                <strong className="text-gray-400">Why this one, and what I looked at instead:</strong> this platform
                needs to embed a growing pool of tens of thousands of resumes and jobs on a small, self-hosted server
                with no GPU, so speed matters as much as raw quality. I checked all-mpnet-base-v2, a stronger sibling
                in the same family, and three models actually built for job or resume matching specifically:
                TechWolf's JobBERT-v2 (public, English, trained on real job ads, but built to match short job titles
                against skill lists, not full descriptions), CareerBERT (a model fine-tuned specifically to match
                resumes to ESCO job categories, exactly the right idea, but trained on German text), and
                conSultantBERT (a Randstad research model trained on 270,000 real resume-vacancy pairs that reportedly
                beats generic models, but never released publicly). Each had a real reason it did not fit. I go
                through the full comparison, with real numbers and links, further down this page.
              </p>
            </div>

            <div className="card p-5">
              <h3 className="font-semibold text-white mb-1">spaCy</h3>
              <p className="text-sm text-gray-400 mb-2">Reads a resume and pulls out structured facts: skills, job titles, companies, dates.</p>
              <p className="text-sm text-gray-300 mb-3">
                Example: given a paragraph of work history, spaCy is what identifies "Senior Data Analyst," "Acme Corp,"
                and "Jan 2021 to Mar 2024" as a single structured entry, and separately picks "Python," "SQL," and "Tableau"
                out as skills. This is how a candidate's skill list and years of experience get built automatically.
              </p>
              <p className="text-sm text-gray-500 border-t border-surface-500 pt-3">
                <strong className="text-gray-400">Why this one, and what I looked at instead:</strong> resumes get
                parsed asynchronously, sometimes in batches, so throughput matters. spaCy's small English pipeline
                processes thousands of words per second on ordinary CPU hardware. Flair and Stanford's Stanza both
                report slightly higher raw accuracy on standard NER benchmarks, but both run several times slower,
                which adds up when many resumes parse at once. NLTK, the older standard Python NLP library, is really
                built for teaching and research, not a production extraction pipeline. I also considered sending
                resumes to a cloud NLP API like AWS Comprehend, but that means sending candidate personal data to a
                third party and paying per request at scale, which I would rather avoid. I did not use spaCy's own
                larger transformer pipeline either, for the same reason: meaningfully slower for a modest accuracy gain.
              </p>
            </div>

            <div className="card p-5">
              <h3 className="font-semibold text-white mb-1">GradientBoostingClassifier</h3>
              <p className="text-sm text-gray-400 mb-2">Combines the semantic score, skill overlap, experience, and education into one final match percentage.</p>
              <p className="text-sm text-gray-300 mb-3">
                This is the model that's actually trained. Everything above feeds into it as input; it learns from
                labeled examples of who was hired versus rejected which combination of factors actually predicted a
                good match, and it's what SHAP and LIME explain when you click "Explain" on a match score.
              </p>
              <p className="text-sm text-gray-500 border-t border-surface-500 pt-3">
                <strong className="text-gray-400">Why this one, and what I looked at instead:</strong> it ships as
                part of scikit-learn, which this project already depends on, so it adds no extra install to the
                deployed container. XGBoost is generally the stronger performer for this kind of small tabular
                classification task, and the code already switches to it automatically the moment it is installed,
                but adding a large compiled dependency was not worth it until there was enough real training data to
                make the upgrade matter. LightGBM and CatBoost are comparable, well-regarded alternatives in the same
                family that I have not specifically evaluated for this project.
              </p>
            </div>

            <div className="card p-5">
              <h3 className="font-semibold text-white mb-1">SHAP &amp; LIME</h3>
              <p className="text-sm text-gray-400 mb-2">Explain, after the fact, why the GradientBoostingClassifier gave the score it gave.</p>
              <p className="text-sm text-gray-300 mb-3">
                Example: instead of just showing "78% match," the explanation shows "+12% for skill overlap, +9% for
                semantic similarity, and minus 4% for experience gap," so a recruiter can see the actual reasoning, not
                just trust a number.
              </p>
              <p className="text-sm text-gray-500 border-t border-surface-500 pt-3">
                <strong className="text-gray-400">Why both, and what I looked at instead:</strong> they make different
                tradeoffs, and showing both means a recruiter is not trusting a single method blindly. SHAP is the
                more rigorous of the two, grounded in game theory, and gives the same answer every time you ask it.
                LIME is faster and gives a quick local approximation, but it can give a slightly different answer if
                asked twice for the same prediction, since it works by sampling nearby examples rather than an exact
                calculation. I also looked at Anchors, which explains a prediction as a rule rather than a set of
                weighted factors, but it answers a different question than "why this score," so it felt like a
                separate feature rather than a replacement for either of these.
              </p>
            </div>
          </div>
        </section>

        {/* Reliability */}
        <section className="space-y-4 mb-12">
          <h2 className="section-title">How reliable is each of these, honestly?</h2>
          <p className="text-gray-300 leading-relaxed">
            I'd rather tell you exactly what I can and can't back up than let a slick UI imply more than is true.
          </p>
          <ul className="space-y-4">
            <li className="text-gray-300 leading-relaxed">
              <strong className="text-white">SBERT</strong>: I am not claiming a number of my own here. This is a
              pretrained model (all-MiniLM-L6-v2), and its accuracy has already been measured by the people who built
              it, not by me. On the STS Benchmark, a standard test of how well a model judges two sentences as similar
              in meaning, it is commonly reported to score in the mid-80s out of 100. On the broader MTEB benchmark, a
              suite of 56 different language tasks, it averages in the mid-50s out of 100, which is expected since that
              suite tests far more than just similarity matching. I want to be upfront that I saw slightly different
              exact numbers depending on which evaluation writeup I checked (the mid-80s figure ranged from about 82 to
              85 across sources), which is normal since benchmark scores can shift a little as evaluation code and
              dataset versions get updated over time. Rather than freeze one exact decimal here that could go stale,
              here are the actual live sources for the current number: the model's own {' '}
              <a href="https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2" target="_blank" rel="noopener noreferrer" className="text-scarlet-400 hover:text-scarlet-300 underline decoration-scarlet-800">page on Hugging Face</a>
              {' '}and the public{' '}
              <a href="https://huggingface.co/spaces/mteb/leaderboard" target="_blank" rel="noopener noreferrer" className="text-scarlet-400 hover:text-scarlet-300 underline decoration-scarlet-800">MTEB leaderboard</a>.
              What matters most for this platform: that score measures general sentence similarity, not
              hiring success, so it should be read as this model's reputation on its own task, never as this
              platform's accuracy.
            </li>
            <li className="text-gray-300 leading-relaxed">
              <strong className="text-white">spaCy</strong>: this is the one piece I can actually measure honestly, and
              unlike the other two, I actually did. Does it correctly pull the right skills out of a real resume? That's
              a real precision and recall question I can check by hand against real text, independent of whether I have
              hiring outcome data at all. So I did it: I sampled 16 real candidates at random from the imported datasets
              (excluding the audit study below, whose "resumes" are short fabricated bio stubs by design, not full
              resumes), read each one myself, and wrote down the skills a recruiter would reasonably tag before looking
              at what the extractor produced. Across those 16 people (59 true positives, 4 false positives, 8 false
              negatives), extraction came out to <strong className="text-white">93.7% precision and 88.1% recall</strong> (F1
              90.8%). It also caught two real mistakes worth naming instead of hiding: it tagged "typescript" on a
              resume that never mentions JavaScript or TypeScript once (it's an Oracle/SQL database administrator's CV),
              and "statistics" on a SQL Server admin's resume that never uses that word either. Both are named,
              reproducible false positives, not swept under the rug. This is a small, honest sample, not a claim about
              accuracy across all 13,000+ real candidates, and it's a fixed, re-runnable check
              (<code className="text-xs bg-surface-600 px-1.5 py-0.5 rounded">ml/nlp/skill_extraction_eval.py</code>), not
              a one-time number I'm asking you to trust blindly.
            </li>
            <li className="text-gray-300 leading-relaxed">
              <strong className="text-white">GradientBoostingClassifier</strong>: I want to be extra careful here, so I
              checked the real numbers instead of just repeating what I said before. The model saved on this platform
              right now was trained on 251 examples. Of those, 26 are marked as hired and 225 are marked as not hired.
              All 251 of them are synthetic. None are real people. So if I gave you an accuracy number for this model
              today, it would only tell you how well it agrees with this platform's own made up hiring simulation, not
              how well it predicts real hiring. I am not going to call that "accuracy," because it would not be true.
            </li>
            <li className="text-gray-300 leading-relaxed">
              Here is the part I actually dug into. There is one dataset with real hiring outcomes: the audit study
              described further down this page, with 4,870 real decisions. That data is sitting in the database. It
              just never made it into this model's training, and I found out exactly why. A small piece of code copies
              a real hiring outcome onto a match score, but it only runs the moment someone applies to a job, and only
              if a match score for that person already exists at that exact moment. For most of these real
              applications, matching had not run yet when they were imported, so that copy step found nothing to
              update and never tried again later.
            </li>
            <li className="text-gray-300 leading-relaxed">
              This was fixable, so I fixed it. I wrote a script that scores every one of those 4,812 real application
              pairs that never had a match score, using only what was already sitting in the database: real resumes,
              real jobs, and the real skills and embeddings already extracted from them during import. Nothing new
              was downloaded or added. Then I labeled all 4,870 real applications the way the study itself actually
              measured success: 392 real callbacks as the positive outcome, 4,478 real non-callbacks as the negative
              outcome. That is now sitting in the database as real, correctly labeled data.
            </li>
            <li className="text-gray-300 leading-relaxed">
              I also fixed the actual bug, not just the backlog it left behind. The matching code now checks, every
              time it runs for a job, whether a real hiring decision already exists for that job, and relabels the
              results to match. So the same gap should not happen again for any future real decision, on any job, not
              just this one dataset.
            </li>
            <li className="text-gray-300 leading-relaxed">
              I have not retrained the saved model on this new real data, and I want to explain the actual reason,
              not just call it a future step. The audit study's own researchers designed it to hold resume quality
              roughly constant and randomize one thing: a name signaling race and gender, so they could isolate its
              effect on callbacks. That means whether someone got a callback in this data was driven substantially
              by a signal I deliberately never feed into this classifier at all, since protected attributes are
              excluded from matching on purpose. Training a model built on semantic similarity, skill overlap,
              experience, and education against outcomes that were mostly explained by something outside those
              inputs would not teach it what makes a good match. It would just fit whatever weak, coincidental
              patterns happen to exist between my features and an outcome that is mostly noise as far as those
              features are concerned.
            </li>
            <li className="text-gray-300 leading-relaxed">
              There is a second reason on top of that. Every one of these 4,870 real examples comes from one
              narrow slice: entry level clerical and sales jobs, in two U.S. cities, over twenty years ago. If I
              trained on that and then used the result to score, say, a senior engineering role or a nurse
              practitioner role today, I would be trusting a model far outside anything it was ever actually
              validated on. Good practice means not deploying a model past the range it was tested on, and right
              now that range is one narrow study, not a broad picture of real hiring.
            </li>
            <li className="text-gray-300 leading-relaxed">
              <strong className="text-white">The name-bias probe</strong>: unlike the classifier above, this one has a
              real, already-run result, not just a plan. I explain the full test further down this page, but the number
              itself: across 300 real candidate and job pairs and 24 real-name variants per resume, average score
              movement between White-coded and Black-coded names was 0.0019, statistically indistinguishable from zero.
              There was some sensitivity to a name being present at all (about 0.056 on average), but it didn't
              consistently favor either group. It's a small, bounded test, not a certification that bias is impossible,
              but it's a real number from a real run, reproducible any time from
              {' '}<code className="text-xs bg-surface-600 px-1.5 py-0.5 rounded">ml/fairness/name_bias_probe.py</code>.
            </li>
            <li className="text-gray-300 leading-relaxed">
              <strong className="text-white">A bug I found and fixed while checking my own work</strong>: while
              verifying the real data I'd just imported, I noticed match scores that looked wrong (several came out to
              a suspicious exact 1.0). I traced it back. The weights actually driving the match score had been trained
              on this platform's own synthetic hiring simulator, and that simulator deliberately decides who gets hired
              using skill overlap and education, on purpose, decoupled from semantic similarity. It's a fixture for
              testing the fairness code, not a source of truth about what makes a good match. Training weights against
              it taught the model to assign SBERT's semantic score a weight of essentially zero. I also found the
              education comparison was hardcoded to assume every job requires a bachelor's degree, even when a real job
              posting said otherwise or said nothing at all. I fixed both problems. I reverted to principled fixed
              weights until there's real per-organization decision data to learn from responsibly, and I made the
              education check use each job's actual stated requirement (or treat an unstated one as not held against a
              candidate, rather than assuming a degree was always required). I'm disclosing this because a platform
              built around "explainable, audited scoring" has to hold itself to that standard when it gets something
              wrong internally, not just when auditing someone else's decisions.
            </li>
            <li className="text-gray-300 leading-relaxed">
              <strong className="text-white">The fairness math itself</strong>: disparate impact ratio and the 4/5ths
              rule are just arithmetic applied to whatever real decisions exist in the system. Once an organization has
              real shortlist, hire, or reject decisions logged, this number is exactly as reliable as their own data
              entry. This is the one part of the platform I can call fully reliable, because it isn't a prediction, it's
              a calculation.
            </li>
          </ul>
        </section>

        {/* Counterfactual name-bias probe */}
        <section className="space-y-4 mb-12">
          <h2 className="section-title">A fairness check I actually ran, not just claimed</h2>
          <p className="text-gray-300 leading-relaxed">
            Protected attributes (gender, ethnicity, age, disability) are never fed into the matching model as inputs.
            I can point to the exact code that proves that. But there's a subtler problem that guarantee doesn't cover: a
            resume's free text can still carry someone's name, and a name can carry racial or gender signal even though
            no explicit "race" or "gender" field was ever touched. This is the same failure mode the audit study above
            was built to catch, so I decided to actually test for it rather than just assert it isn't happening.
          </p>
          <p className="text-gray-300 leading-relaxed">
            The test: take a real candidate's resume, hold every word of it completely fixed, and swap in nothing but a
            different first name. Twenty-four of them, six each from the actual most common White-female, White-male,
            Black-female, and Black-male coded names in the audit study data above (real names from a real published
            study, not ones I made up). Re-run the match score against the same job for each variant. If the model
            genuinely doesn't care about names, all 24 scores should land in about the same place.
          </p>
          <p className="text-gray-300 leading-relaxed">
            I ran this across 300 real candidate and job pairs. The result: average score for White-coded names came out
            0.0019 <em>lower</em> than Black-coded names, which is statistically indistinguishable from zero and not a
            meaningful gap in either direction. There was some sensitivity to a name being present at all (scores moved
            by about 0.056 on average across the 24 variants for the same resume), but not in a way that consistently
            favored one racial group. I'd rather publish a real, slightly messy number than not run the test at all.
            This check is in the codebase (<code className="text-xs bg-surface-600 px-1.5 py-0.5 rounded">ml/fairness/name_bias_probe.py</code>)
            and can be re-run any time, at any scale, on real candidate data.
          </p>
          <p className="text-gray-300 leading-relaxed text-sm">
            I also wrote down, in plain terms, what I actually expect responsible use of this platform to look like:
            {' '}<Link to="/governance" className="text-scarlet-400 hover:text-scarlet-300 underline decoration-scarlet-800">how I expect this platform to be used</Link>.
          </p>
        </section>

        {/* Data sources */}
        <section className="space-y-4 mb-12">
          <h2 className="section-title">Where the real data in this platform comes from</h2>
          <p className="text-gray-300 leading-relaxed">
            Everything you see that isn't synthetic (generated to test the fairness features against known, controlled
            bias scenarios) comes from one of the eight public datasets below. I sourced every one of them myself,
            checked each one's license directly, and I'm listing exactly what I used and how much.
          </p>
          <p className="text-gray-300 leading-relaxed text-sm">
            Two more I looked at and decided <strong>not</strong> to use, for the record. One is a well-known 2012
            Kaggle competition dataset, CareerBuilder's Job Recommendation Challenge, that actually has what almost
            nothing else does: real records of who applied to which real job posting. I didn't use it because Kaggle's
            competition rules restrict that data to non-commercial use and forbid redistributing it outside the
            competition's original participants, which conflicts with treating this as a real product. The other is a
            real application-interaction dataset from XING's 2016 and 2017 RecSys Challenge, which I looked into but
            it turned out to never have been released publicly at all. It was only accessible to registered competitors
            during the competition window. Not a judgment call on that one, it's simply not obtainable.
          </p>

          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="text-left text-gray-500 text-xs uppercase tracking-wide border-b border-surface-400">
                  <th className="py-2 pr-4">Dataset</th>
                  <th className="py-2 pr-4">What I used</th>
                  <th className="py-2 pr-4">License</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-400">
                {DATASETS.map((d) => (
                  <tr key={d.name}>
                    <td className="py-3 pr-4 align-top">
                      <a href={d.href} target="_blank" rel="noopener noreferrer" className="text-white hover:text-scarlet-400 transition-colors inline-flex items-start gap-1">
                        {d.name} <ExternalLink className="w-3 h-3 flex-shrink-0 mt-1" />
                      </a>
                      <p className="text-xs text-gray-500 mt-0.5">{d.what}</p>
                    </td>
                    <td className="py-3 pr-4 align-top text-gray-300">{d.used}</td>
                    <td className="py-3 pr-4 align-top text-gray-300">
                      {d.licenseHref ? (
                        <a href={d.licenseHref} target="_blank" rel="noopener noreferrer" className="hover:text-scarlet-400 transition-colors underline decoration-gray-600">
                          {d.license}
                        </a>
                      ) : d.license}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="text-gray-300 leading-relaxed text-sm">
            I deduplicated real data across every one of these sources myself. Before importing any resume or job
            posting, I check it against everything already in the system by content, not just by source, so the same
            real resume or job posting (including cases where two different datasets happen to scrape the same original
            source, like livecareer.com) only ever gets counted once.
          </p>

          <p className="text-gray-300 leading-relaxed text-sm">
            On the two sources I want to be extra direct about: the <strong>LinkedIn Job Postings</strong> dataset was
            originally scraped from LinkedIn, and LinkedIn's own Terms of Service prohibit scraping. That's true
            regardless of the Creative Commons license the Kaggle uploader attached to their republished copy, since
            that license only covers what the uploader actually had the right to license. And the{' '}
            <strong>Resume-Classification-Dataset</strong> contains real people's resumes gathered partly through Google
            and Bing image search; its own README notes this raises personal-information exposure concerns. I'm
            including both anyway, as a portfolio decision I made with full awareness of both issues, and I'm disclosing
            that plainly here rather than glossing over it.
          </p>

          <p className="text-gray-300 leading-relaxed text-sm">
            For every real candidate imported from any of these sources, I deliberately leave gender, ethnicity, age
            range, and disability status blank. I never had that information, and I'm not going to guess it about a real
            person just to make a demo look more complete. There's exactly one exception, and it's a deliberate one. The
            audit study candidates aren't real people. They're fictional resumes the original researchers constructed
            specifically to test race and gender bias, and race and gender were literally the variable they controlled
            and published. For those records only, I populate ethnicity and gender, explicitly labeled as "name-coded,
            audit study" rather than presented as if a real person self-reported them. Outside that one dataset, only
            the fully synthetic dataset (generated, not based on any real person) models those attributes, specifically
            so the fairness audit has something realistic to test itself against.
          </p>
        </section>

        {/* Contact / takedown */}
        <section className="space-y-3 mb-4">
          <h2 className="section-title">If you're a rights holder</h2>
          <p className="text-gray-300 leading-relaxed text-sm">
            If any of the data above is yours and you'd like it removed from this project, I'll take it down. Email me
            with a link to the specific dataset or record and I'll act on it directly. I'm not going to make you go
            through a formal process for something I can just fix.
          </p>
          <a
            href="mailto:sheikh.k.m.m.tahmid@gmail.com"
            className="inline-flex items-center gap-2 text-sm text-scarlet-400 hover:text-scarlet-300 transition-colors"
          >
            <Mail className="w-4 h-4" /> sheikh.k.m.m.tahmid@gmail.com
          </a>
        </section>
      </div>
    </div>
  )
}
