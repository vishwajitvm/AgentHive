import React from 'react';

interface JsonViewerProps {
  data: any;
}

export default function JsonViewer({ data }: JsonViewerProps) {
  const formatJson = (json: any) => {
    if (typeof json !== 'string') {
      json = JSON.stringify(json, null, 2);
    }
    
    // Replace escaped newlines with actual newlines in strings
    json = json.replace(/\\n/g, '\n');

    const jsonRegex = /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g;
    
    return json.replace(jsonRegex, (match: string) => {
      let cls = 'text-sky-400'; // number
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          cls = 'text-emerald-400 font-semibold'; // key
        } else {
          cls = 'text-amber-300 whitespace-pre-wrap leading-relaxed'; // string
        }
      } else if (/true|false/.test(match)) {
        cls = 'text-rose-400 font-bold'; // boolean
      } else if (/null/.test(match)) {
        cls = 'text-slate-500 italic'; // null
      }
      return `<span class="${cls}">${match}</span>`;
    });
  };

  return (
    <pre 
      className="text-[11px] font-mono bg-slate-900 p-5 rounded-xl border border-slate-800 overflow-x-auto max-h-[500px] overflow-y-auto"
      dangerouslySetInnerHTML={{ __html: formatJson(data) }}
    />
  );
}
