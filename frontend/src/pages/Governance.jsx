import { Link } from 'react-router-dom'
import { ArrowLeft, Mail } from 'lucide-react'
import LogoIcon from '../components/LogoIcon'

export default function Governance() {
  return (
    <div className="min-h-screen bg-surface-900 text-white">
      <div className="max-w-3xl mx-auto px-6 py-12">
        <Link to="/about" className="inline-flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors mb-8">
          <ArrowLeft className="w-4 h-4" /> Back to About
        </Link>

        <div className="flex items-center gap-3 mb-8">
          <LogoIcon size={40} />
          <div>
            <h1 className="page-title">How I expect this platform to be used</h1>
            <p className="text-sm text-gray-500">A real policy, not a legal disclaimer nobody reads.</p>
          </div>
        </div>

        <section className="space-y-4 mb-12">
          <h2 className="section-title">Why this page exists</h2>
          <p className="text-gray-300 leading-relaxed">
            A tool built around auditing fairness could, in the wrong hands, be used to do the opposite of what it's
            for. Someone could point to a clean fairness report as cover while making decisions some other way
            entirely. I can't stop that with code alone, but I can be explicit about what responsible use actually
            looks like, so there's no ambiguity about what this platform is meant to support and what it is not.
          </p>
        </section>

        <section className="space-y-4 mb-12">
          <h2 className="section-title">A human makes the final call, every time</h2>
          <p className="text-gray-300 leading-relaxed">
            This platform never automatically rejects or automatically hires anyone. It ranks and explains. A person
            has to actually change an application's status for anything to happen, and that person is recorded by
            name, not just "the system." Look at the code and you'll find there is no path from a match score straight
            to a rejection without a human in between. If a version of this were ever built that removed that human
            step to move faster, it would no longer be the same product, and I would not call it fair.
          </p>
        </section>

        <section className="space-y-4 mb-12">
          <h2 className="section-title">The decision record cannot be quietly rewritten</h2>
          <p className="text-gray-300 leading-relaxed">
            Every time an application's status changes, that change is written to a permanent history table, not just
            overwritten on the application itself. Who changed it, when, from what status to what status, is kept
            forever. If an organization's hiring pattern is ever questioned later, the honest answer to "what actually
            happened here" already exists and cannot be edited after the fact to look better than it was.
          </p>
          <p className="text-gray-300 leading-relaxed">
            That same history now also records something else: whether a decision agreed or disagreed with what the
            AI's ranking would have suggested. Not to grade the recruiter, and not to grade the AI, but because a
            pattern of disagreement that lines up with a candidate's protected attributes is itself a real fairness
            signal, and it would be dishonest to build an audit tool that only looks at the AI's output and never
            looks at how humans actually used it.
          </p>
        </section>

        <section className="space-y-4 mb-12">
          <h2 className="section-title">A fairness report is not a certificate</h2>
          <p className="text-gray-300 leading-relaxed">
            A disparate impact ratio, on its own, out of context, can be made to say almost anything. My rule for this
            platform: a fairness number is never shown, exported, or referenced without also showing what it's based
            on. Specifically, whether it comes from real hiring decisions or a provisional AI-rank estimate, how many
            decisions it's based on, and when it was generated. An organization with five real decisions and an
            organization with five thousand should never be able to present the same-looking "we passed" badge. If you
            build something on top of this platform's data, I'd ask you to keep that same discipline: never strip a
            fairness number away from the context that makes it honest.
          </p>
        </section>

        <section className="space-y-4 mb-12">
          <h2 className="section-title">What is supposed to happen when bias is flagged</h2>
          <p className="text-gray-300 leading-relaxed">
            When a disparate impact ratio drops below the 4/5ths threshold, the platform flags it and logs a warning.
            That flag is not the end of the process, it's the start of one. The intent is that a flagged result gets
            looked at by a person who asks why, not silently dismissed, and not used to justify a decision that was
            already made. I have not built an enforcement mechanism that forces this to happen, because I don't think
            a piece of software can force an organization to act in good faith. What I can do, and have done, is make
            sure the flag is impossible to miss and the underlying data behind it is real and traceable.
          </p>
        </section>

        <section className="space-y-4 mb-12">
          <h2 className="section-title">Protected attributes are never a model input</h2>
          <p className="text-gray-300 leading-relaxed">
            Gender, ethnicity, age range, and disability status are collected for exactly one purpose: auditing
            whether real decisions were fair across those groups. They are never passed into the matching model as a
            feature, and I mean that as a concrete, checkable claim, not a promise. Look at
            {' '}<code className="text-xs bg-surface-600 px-1.5 py-0.5 rounded">ml/matching/scorer.py</code>, specifically
            {' '}<code className="text-xs bg-surface-600 px-1.5 py-0.5 rounded">build_feature_vector</code>, and you will
            find skills, experience, and education. Nothing else. The counterfactual name-bias check described on the
            About page exists because I know a promise like this one is worth almost nothing without someone actually
            testing for the ways it could still fail in practice.
          </p>
        </section>

        <section className="space-y-3 mb-4">
          <h2 className="section-title">If something here doesn't hold up</h2>
          <p className="text-gray-300 leading-relaxed text-sm">
            I already found and fixed one real bug in my own scoring pipeline this way, described on the About page.
            If you find another gap between what this page says and what the code actually does, I want to know about
            it. Email me directly.
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
