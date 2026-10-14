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
    <div className="my-4 rounded-xl border border-slate-300 bg-slate-900 overflow-hidden shadow-sm font-mono text-xs sm:text-sm">
      {/* Code Header Bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700 text-slate-300 text-xs">
        <span className="font-mono text-slate-200 font-semibold uppercase tracking-wider text-[11px]">
          {language || 'code'}
        </span>
        <button
          onClick={handleCopy}
          type="button"
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 hover:text-white transition-colors text-[11px] font-medium border border-slate-600"
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
      <div className="p-4 overflow-x-auto text-slate-100 leading-relaxed font-mono">
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
      className="px-1.5 py-0.5 mx-0.5 text-xs font-mono rounded bg-slate-100 text-blue-700 border border-slate-200 inline-block align-middle font-medium"
      {...props}
    >
      {children}
    </code>
  );
};

export const LLMMessageRenderer = ({ content }) => {
  if (!content) return null;

  let safeContent = typeof content === 'string' ? content : String(content);

  // Fail-safe 1: Remove markdown code fences
  safeContent = safeContent.replace(/```json[\s\S]*?```/gi, '');

  // Fail-safe 2: Remove any JSON container (arrays or objects) containing quiz keys ("quiz", "questions", "question", "options")
  const quizKeys = ['"quiz"', "'quiz'", '"questions"', "'questions'", '"question"', "'question'", '"options"', "'options'"];
  let lower = safeContent.toLowerCase();

  let foundKeyIdx = -1;
  for (const k of quizKeys) {
    let p = lower.indexOf(k);
    if (p !== -1 && (foundKeyIdx === -1 || p < foundKeyIdx)) {
      foundKeyIdx = p;
    }
  }

  while (foundKeyIdx !== -1) {
    // Scan backwards from foundKeyIdx to find outermost opening container '{' or '['
    let startIdx = -1;
    let pos = foundKeyIdx;
    while (pos >= 0) {
      let ch = safeContent[pos];
      if (ch === '{' || ch === '[') {
        startIdx = pos;
        let prevPos = pos - 1;
        while (prevPos >= 0) {
          let prevCh = safeContent[prevPos];
          if (prevCh === ' ' || prevCh === '\t' || prevCh === '\n' || prevCh === '\r' || prevCh === ',') {
            prevPos--;
            continue;
          } else if (prevCh === '[' || prevCh === '{') {
            startIdx = prevPos;
            pos = prevPos;
            break;
          } else {
            break;
          }
        }
        if (startIdx === pos) break;
      }
      pos--;
    }

    if (startIdx !== -1) {
      let stack = [];
      let endIdx = -1;
      let inString = false;
      let escape = false;

      for (let i = startIdx; i < safeContent.length; i++) {
        let ch = safeContent[i];
        if (escape) {
          escape = false;
          continue;
        }
        if (ch === '\\') {
          escape = true;
          continue;
        }
        if (ch === '"') {
          inString = !inString;
          continue;
        }
        if (!inString) {
          if (ch === '{' || ch === '[') {
            stack.push(ch);
          } else if (ch === '}' || ch === ']') {
            if (stack.length > 0) {
              let top = stack[stack.length - 1];
              if ((ch === '}' && top === '{') || (ch === ']' && top === '[')) {
                stack.pop();
                if (stack.length === 0) {
                  endIdx = i;
                  break;
                }
              }
            }
          }
        }
      }

      if (endIdx !== -1) {
        safeContent = safeContent.slice(0, startIdx) + safeContent.slice(endIdx + 1);
      } else {
        safeContent = safeContent.slice(0, startIdx);
      }
    } else {
      break;
    }

    lower = safeContent.toLowerCase();
    foundKeyIdx = -1;
    for (const k of quizKeys) {
      let p = lower.indexOf(k);
      if (p !== -1 && (foundKeyIdx === -1 || p < foundKeyIdx)) {
        foundKeyIdx = p;
      }
    }
  }

  // Fail-safe 3: Clean quiz section headings and intro lines
  safeContent = safeContent.replace(/(?:\r?\n)?\s*#{1,3}\s*Quiz[\s\S]*$/i, '');
  safeContent = safeContent.replace(/(?:\r?\n)?\s*To help you check your understanding[\s\S]*$/i, '');
  safeContent = safeContent.replace(/(?:\r?\n)?\s*Here are (?:some|\d+)?\s*(?:questions|multiple-choice questions)[\s\S]*$/i, '');
  safeContent = safeContent.replace(/(?:\r?\n)?\s*Test your understanding[\s\S]*$/i, '');

  safeContent = safeContent.trim();

  return (
    <div className="llm-message-content max-w-none text-slate-800 leading-relaxed text-sm sm:text-base font-sans space-y-3">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1({ children }) {
            return (
              <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 mt-6 mb-3 pb-2 border-b border-slate-200 flex items-center gap-2">
                {children}
              </h1>
            );
          },
          h2({ children }) {
            return (
              <h2 className="text-lg sm:text-xl font-bold text-blue-700 mt-5 mb-2.5 pb-1 border-b border-slate-200">
                {children}
              </h2>
            );
          },
          h3({ children }) {
            return (
              <h3 className="text-base sm:text-lg font-semibold text-indigo-800 mt-4 mb-2">
                {children}
              </h3>
            );
          },
          h4({ children }) {
            return (
              <h4 className="text-sm sm:text-base font-semibold text-slate-900 mt-3 mb-1.5">
                {children}
              </h4>
            );
          },
          p({ children }) {
            return (
              <p className="text-slate-700 leading-relaxed mb-3.5 last:mb-0 text-sm sm:text-base">
                {children}
              </p>
            );
          },
          ul({ children }) {
            return (
              <ul className="list-disc list-outside ml-5 space-y-1.5 my-3 text-slate-700 text-sm sm:text-base marker:text-blue-600">
                {children}
              </ul>
            );
          },
          ol({ children }) {
            return (
              <ol className="list-decimal list-outside ml-5 space-y-1.5 my-3 text-slate-700 text-sm sm:text-base marker:text-blue-600 marker:font-bold">
                {children}
              </ol>
            );
          },
          li({ children }) {
            return (
              <li className="pl-1 leading-relaxed text-slate-700">
                {children}
              </li>
            );
          },
          strong({ children }) {
            return (
              <strong className="font-bold text-slate-900 bg-blue-50 px-1 py-0.5 rounded text-blue-900 border border-blue-200">
                {children}
              </strong>
            );
          },
          em({ children }) {
            return <em className="italic text-slate-800">{children}</em>;
          },
          blockquote({ children }) {
            return (
              <blockquote className="border-l-4 border-blue-500 bg-blue-50/60 px-4 py-3 my-4 rounded-r-2xl text-slate-700 italic border-y border-r border-slate-200 shadow-xs">
                {children}
              </blockquote>
            );
          },
          table({ children }) {
            return (
              <div className="overflow-x-auto my-4 rounded-xl border border-slate-200 bg-white shadow-xs">
                <table className="w-full text-left text-xs sm:text-sm text-slate-800 border-collapse">
                  {children}
                </table>
              </div>
            );
          },
          thead({ children }) {
            return (
              <thead className="bg-slate-50 text-slate-800 font-bold border-b border-slate-200 uppercase tracking-wider text-[11px]">
                {children}
              </thead>
            );
          },
          tbody({ children }) {
            return <tbody className="divide-y divide-slate-200">{children}</tbody>;
          },
          tr({ children }) {
            return (
              <tr className="hover:bg-slate-50/60 transition-colors">
                {children}
              </tr>
            );
          },
          th({ children }) {
            return (
              <th className="px-4 py-3 font-bold text-slate-800 border-b border-slate-200">
                {children}
              </th>
            );
          },
          td({ children }) {
            return (
              <td className="px-4 py-2.5 text-slate-700 border-b border-slate-100">
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
                className="text-blue-600 hover:text-blue-700 underline underline-offset-4 font-medium transition-colors"
              >
                {children}
              </a>
            );
          },
          hr() {
            return <hr className="my-6 border-t border-slate-200" />;
          },
          pre: CodeBlock,
          code: InlineCode,
        }}
      >
        {safeContent}
      </ReactMarkdown>
    </div>
  );
};

export default LLMMessageRenderer;
