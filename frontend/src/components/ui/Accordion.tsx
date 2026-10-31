import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';

export interface AccordionItem {
  id: string;
  question: string;
  answer: string;
}

export interface AccordionProps {
  items: AccordionItem[];
  allowMultiple?: boolean;
  className?: string;
}

export const Accordion: React.FC<AccordionProps> = ({ items, allowMultiple = false, className = '' }) => {
  const [openIds, setOpenIds] = useState<string[]>([]);

  const toggle = (id: string) => {
    if (allowMultiple) {
      setOpenIds(prev => (prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]));
    } else {
      setOpenIds(prev => (prev.includes(id) ? [] : [id]));
    }
  };

  return (
    <div className={`divide-y divide-slate-200 border border-slate-200 rounded-xl overflow-hidden bg-white shadow-sm ${className}`}>
      {items.map(item => {
        const isOpen = openIds.includes(item.id);
        return (
          <div key={item.id} className="transition">
            <button
              onClick={() => toggle(item.id)}
              className="w-full py-4 px-6 text-left flex items-center justify-between gap-4 font-semibold text-slate-800 hover:text-brand-navy hover:bg-slate-50/70 transition"
              aria-expanded={isOpen}
            >
              <span className="text-sm font-bold text-slate-900">{item.question}</span>
              <ChevronDown
                className={`w-4 h-4 text-slate-500 shrink-0 transition-transform duration-200 ${
                  isOpen ? 'transform rotate-180 text-brand-teal' : ''
                }`}
              />
            </button>
            {isOpen && (
              <div className="px-6 pb-5 pt-1 text-sm text-slate-600 leading-relaxed border-t border-slate-50 bg-slate-50/30">
                {item.answer}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
