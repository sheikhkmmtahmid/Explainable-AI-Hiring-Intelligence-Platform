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
              <p className="text-sm text-gray-300">
                Example: a resume that says "built REST APIs with Django" and a job that asks for "backend web service
                development experience" share almost no exact words, but SBERT recognizes they mean nearly the same
                thing. This is what powers the semantic-similarity part of every match score.
              </p>
            </div>

            <div className="card p-5">
              <h3 className="font-semibold text-white mb-1">spaCy</h3>
              <p className="text-sm text-gray-400 mb-2">Reads a resume and pulls out structured facts: skills, job titles, companies, dates.</p>
              <p className="text-sm text-gray-300">
                Example: given a paragraph of work history, spaCy is what identifies "Senior Data Analyst," "Acme Corp,"
                and "Jan 2021 to Mar 2024" as a single structured entry, and separately picks "Python," "SQL," and "Tableau"
                out as skills. This is how a candidate's skill list and years of experience get built automatically.
              </p>
            </div>

            <div className="card p-5">
              <h3 className="font-semibold text-white mb-1">GradientBoostingClassifier</h3>
              <p className="text-sm text-gray-400 mb-2">Combines the semantic score, skill overlap, experience, and education into one final match percentage.</p>
              <p className="text-sm text-gray-300">
                This is the model that's actually trained. Everything above feeds into it as input; it learns from
                labeled examples of who was hired versus rejected which combination of factors actually predicted a
                good match, and it's what SHAP and LIME explain when you click "Explain" on a match score.
              </p>
            </div>

            <div className="card p-5">
              <h3 className="font-semibold text-white mb-1">SHAP &amp; LIME</h3>
              <p className="text-sm text-gray-400 mb-2">Explain, after the fact, why the GradientBoostingClassifier gave the score it gave.</p>
              <p className="text-sm text-gray-300">
                Example: instead of just showing "78% match," the explanation shows "+12% for skill overlap, +9% for
                semantic similarity, and minus 4% for experience gap," so a recruiter can see the actual reasoning, not
                just trust a number.
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
              <strong className="text-white">SBERT</strong>: I'm not claiming a number of my own here. It's a pretrained
              model with its own published, independently verified benchmarks from the research that created it. Those
              benchmarks measure general semantic similarity, not specifically "predicting hiring success," so I'm citing
              its reputation, not inventing an accuracy figure.
            </li>
            <li className="text-gray-300 leading-relaxed">
              <strong className="text-white">spaCy</strong>: this is the one piece I can actually measure honestly. Does
              it correctly pull the right skills and job titles out of a real resume? That's a real precision and recall
              question I can check by hand against real text, independent of whether I have hiring outcome data at all.
            </li>
            <li className="text-gray-300 leading-relaxed">
              <strong className="text-white">GradientBoostingClassifier</strong>: this is the one I want to be most
              careful about. I cannot honestly report a general real-world accuracy number for this model, and here's
              exactly why. An accuracy number requires a ground truth to measure against: actual hire or reject decisions
              tied to actual resumes and actual job postings, at a scale and breadth that generalizes. I looked,
              specifically, for a public dataset like that. It effectively doesn't exist at production scale, because
              that data is commercially sensitive HR data companies don't publish. There is one narrow, real exception,
              described below, but it's a 2001 to 2002 study of entry-level clerical and sales roles in two U.S. cities.
              Genuinely real, but far too small and narrow to be a general accuracy claim. So outside that one case, any
              accuracy number I could show you would actually be measuring agreement with a synthetic, self-generated
              heuristic I built for demonstration purposes, not real hiring accuracy. I'd rather tell you that plainly
              than publish a number that looks rigorous but isn't.
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
