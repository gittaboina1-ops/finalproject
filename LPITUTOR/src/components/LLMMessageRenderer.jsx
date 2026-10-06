import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Copy, Check } from 'lucide-react';

const CodeBlock = ({ children }) => {
  const [copied, setCopied] = useState(false);
  const codeProps = React.isValidElement(children) ? children.props : {};
  const className = codeProps.className || '';
  const match = /language-(\w+)/.exec(className);
  const language = match ? match[1] : '';
  const rawCode = codeProps.children ?? children ?? '';
  const codeString = (typeof rawCode === 'string' ? rawCode : String(rawCode)).replace(/\n$/, '');

  const handleCopy = () => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(codeString);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="my-4 rounded-xl border border-slate-800 bg-slate-950 overflow-hidden shadow-lg font-mono text-xs sm:text-sm">
      {/* Code Header Bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-slate-900/90 border-b border-slate-800 text-slate-400 text-xs">
        <span className="font-mono text-slate-300 font-semibold uppercase tracking-wider text-[11px]">
          {language || 'code'}
        </span>
        <button
          onClick={handleCopy}
          type="button"
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors text-[11px] font-medium border border-slate-700/50"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      {/* Code Content */}
      <div className="p-4 overflow-x-auto text-slate-200 leading-relaxed font-mono">
        <pre className="m-0 font-mono">
          <code className={className}>
            {codeString}
          </code>
        </pre>
      </div>
    </div>
  );
};

const InlineCode = ({ node, className, children, ...props }) => {
  return (
    <code
      className="px-1.5 py-0.5 mx-0.5 text-xs font-mono rounded bg-slate-800/90 text-blue-300 border border-slate-700/60 inline-block align-middle font-medium"
      {...props}
    >
      {children}
    </code>
  );
};

export const LLMMessageRenderer = ({ content }) => {
  if (!content) return null;

  return (
    <div className="llm-message-content max-w-none text-slate-200 leading-relaxed text-sm sm:text-base font-sans space-y-3">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1({ children }) {
            return (
              <h1 className="text-xl sm:text-2xl font-extrabold text-white mt-6 mb-3 pb-2 border-b border-slate-800 flex items-center gap-2">
                {children}
              </h1>
            );
          },
          h2({ children }) {
            return (
              <h2 className="text-lg sm:text-xl font-bold text-blue-300 mt-5 mb-2.5 pb-1 border-b border-slate-800/80">
                {children}
              </h2>
            );
          },
          h3({ children }) {
            return (
              <h3 className="text-base sm:text-lg font-semibold text-indigo-300 mt-4 mb-2">
                {children}
              </h3>
            );
          },
          h4({ children }) {
            return (
              <h4 className="text-sm sm:text-base font-semibold text-slate-200 mt-3 mb-1.5">
                {children}
              </h4>
            );
          },
          p({ children }) {
            return (
              <p className="text-slate-300 leading-relaxed mb-3.5 last:mb-0 text-sm sm:text-base">
                {children}
              </p>
            );
          },
          ul({ children }) {
            return (
              <ul className="list-disc list-outside ml-5 space-y-1.5 my-3 text-slate-300 text-sm sm:text-base marker:text-blue-400">
                {children}
              </ul>
            );
          },
          ol({ children }) {
            return (
              <ol className="list-decimal list-outside ml-5 space-y-1.5 my-3 text-slate-300 text-sm sm:text-base marker:text-blue-400 marker:font-bold">
                {children}
              </ol>
            );
          },
          li({ children }) {
            return (
              <li className="pl-1 leading-relaxed text-slate-300">
                {children}
              </li>
            );
          },
          strong({ children }) {
            return (
              <strong className="font-bold text-white bg-blue-500/10 px-1 py-0.5 rounded text-blue-200 border border-blue-500/20">
                {children}
              </strong>
            );
          },
          em({ children }) {
            return <em className="italic text-slate-300">{children}</em>;
          },
          blockquote({ children }) {
            return (
              <blockquote className="border-l-4 border-blue-500 bg-blue-950/20 px-4 py-3 my-4 rounded-r-2xl text-slate-300 italic border-y border-r border-slate-800/60 shadow-inner">
                {children}
              </blockquote>
            );
          },
          table({ children }) {
            return (
              <div className="overflow-x-auto my-4 rounded-2xl border border-slate-800 bg-slate-900/60 shadow-lg">
                <table className="w-full text-left text-xs sm:text-sm text-slate-200 border-collapse">
                  {children}
                </table>
              </div>
            );
          },
          thead({ children }) {
            return (
              <thead className="bg-slate-900 text-blue-300 font-semibold border-b border-slate-800 uppercase tracking-wider text-[11px]">
                {children}
              </thead>
            );
          },
          tbody({ children }) {
            return <tbody className="divide-y divide-slate-800/60">{children}</tbody>;
          },
          tr({ children }) {
            return (
              <tr className="hover:bg-slate-800/30 transition-colors">
                {children}
              </tr>
            );
          },
          th({ children }) {
            return (
              <th className="px-4 py-3 font-bold text-blue-300 border-b border-slate-800">
                {children}
              </th>
            );
          },
          td({ children }) {
            return (
              <td className="px-4 py-2.5 text-slate-300 border-b border-slate-800/60">
                {children}
              </td>
            );
          },
          a({ href, children }) {
            return (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:text-blue-300 underline underline-offset-4 font-medium transition-colors"
              >
                {children}
              </a>
            );
          },
          hr() {
            return <hr className="my-6 border-t border-slate-800" />;
          },
          pre: CodeBlock,
          code: InlineCode,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default LLMMessageRenderer;
