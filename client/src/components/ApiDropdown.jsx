import { ChevronDown, Database, ExternalLink } from 'lucide-react';

export default function ApiDropdown({ links }) {
  return (
    <div className="group relative">
      <button className="flex items-center gap-2 font-bold hover:bg-white/10 px-4 py-2 rounded-xl transition text-lg">
        Multi-Tenant <ChevronDown size={16} className="text-gray-500 group-hover:text-white" />
      </button>
      
      <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-64 bg-[#2f2f2f] border border-white/10 rounded-2xl shadow-2xl p-2 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
        <p className="text-[10px] font-bold text-gray-500 px-3 py-2 uppercase">Your Connected APIs</p>
        {links.map((link, idx) => (
          <div key={idx} className="flex items-center justify-between p-3 hover:bg-white/5 rounded-xl cursor-pointer">
            <div className="flex items-center gap-3">
              <div className="p-1.5 bg-white/10 rounded-lg"><Database size={14}/></div>
              <span className="text-sm font-medium">{link.rename}</span>
            </div>
            <span className="text-[10px] text-gray-500 px-2 bg-black/20 rounded-md">{link.platform}</span>
          </div>
        ))}
        {links.length === 0 && <p className="text-sm text-gray-500 px-3 py-4 text-center">No links found</p>}
      </div>
    </div>
  );
}