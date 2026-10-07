import React, { useEffect, useState, useMemo } from "react";
import { NewsItem } from "../../types";
import { fetchCuratedNews } from "../../api";
import { Newspaper, ExternalLink, Tag, ShieldCheck, Flame, Users } from "lucide-react";

interface NewsViewProps {
  onOpenUrl: (url: string) => void;
}

const CATEGORIES = [
  "All Intel",
  "Transfers & Rumors",
  "LCK & Interviews",
  "Official Dispatches",
  "Meta & Analysis",
] as const;

export const NewsView: React.FC<NewsViewProps> = ({ onOpenUrl }) => {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>("All Intel");

  useEffect(() => {
    fetchCuratedNews().then((data) => {
      setNews(data);
      setLoading(false);
    });
  }, []);

  const filteredNews = useMemo(() => {
    if (selectedCategory === "All Intel") return news;
    return news.filter((item) => item.tag === selectedCategory);
  }, [news, selectedCategory]);

  return (
    <div className="p-4 space-y-4 max-w-4xl mx-auto overflow-y-auto h-full select-none">
      {/* View Header */}
      <div className="pb-1 border-b border-[#1e282d] flex items-center justify-between">
        <div>
          <h2 className="text-xs font-bold text-[#c8aa6e] uppercase tracking-wider flex items-center gap-1.5">
            <Newspaper className="w-3.5 h-3.5 text-[#0ac8b9]" />
            LoL Esports Dispatch & Meta Intel
          </h2>
          <div className="text-[11px] text-[#7e8e9f] mt-0.5">
            Curated journalism from Sheep Esports, Inven Global, Riot Esports & Dot Esports
          </div>
        </div>
        <span className="text-[10px] text-[#0ac8b9] bg-[#0ac8b9]/10 px-2 py-0.5 rounded font-mono">
          Tier 1 Sources
        </span>
      </div>

      {/* Category Filter Pills */}
      <div className="flex flex-wrap items-center gap-1.5">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-3 py-1 rounded text-xs font-semibold transition-all ${
              selectedCategory === cat
                ? "bg-[#c8aa6e] text-[#091428]"
                : "bg-[#0a1420] border border-[#1e282d] text-[#7e8e9f] hover:text-[#f0e6d2] hover:border-[#c8aa6e]/50"
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* News Feed Cards */}
      {loading ? (
        <div className="text-center py-12 text-[#7e8e9f] text-xs">Loading pro dispatch…</div>
      ) : (
        <div className="grid gap-3">
          {filteredNews.map((item) => (
            <div
              key={item.id}
              onClick={() => onOpenUrl(item.url)}
              className="bg-[#0a1420] border border-[#1e282d] hover:border-[#c8aa6e] p-4 rounded-lg cursor-pointer transition-all flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold text-[#0ac8b9] uppercase tracking-wide flex items-center gap-1 bg-[#0ac8b9]/10 px-2 py-0.5 rounded">
                      <Tag className="w-3 h-3" />
                      {item.tag}
                    </span>
                    <span className="text-[10px] text-[#c8aa6e] font-semibold">{item.source}</span>
                  </div>
                  <span className="text-[10px] text-[#7e8e9f]">{item.date}</span>
                </div>

                <h3 className="text-sm font-bold text-[#f0e6d2] mb-1.5 group-hover:text-[#c8aa6e] transition-colors leading-snug">
                  {item.title}
                </h3>
                <p className="text-xs text-[#7e8e9f] leading-relaxed mb-3">{item.summary}</p>
              </div>

              <div className="flex items-center justify-between pt-2.5 border-t border-[#1e282d]/60 text-[10px] text-[#7e8e9f]">
                <span className="flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3 text-[#0ac8b9]" />
                  Verified Authoritative Source
                </span>
                <span className="flex items-center gap-1 text-[#0ac8b9] group-hover:underline font-semibold">
                  Read full breakdown <ExternalLink className="w-3 h-3" />
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Authoritative Outlets Guide Box */}
      <div className="p-3.5 rounded-lg bg-[#0a1420] border border-[#1e282d] space-y-2 mt-4">
        <div className="text-xs font-bold text-[#f0e6d2] flex items-center gap-1.5">
          <Flame className="w-3.5 h-3.5 text-[#ff4655]" />
          About Riot & LoL Esports News Ecosystem
        </div>
        <div className="text-[11px] text-[#7e8e9f] leading-relaxed space-y-1">
          <div>
            <strong className="text-[#f0e6d2]">Sheep Esports (Wooloo):</strong> Undisputed #1 worldwide authority for roster transfers, contract buyouts, and off-season trade scoops with a &gt;98% verified track record.
          </div>
          <div>
            <strong className="text-[#f0e6d2]">Inven Global:</strong> Premier English source for LCK post-match press conferences, Korean coach strategy, and player interviews (Faker, Chovy, ShowMaker).
          </div>
          <div>
            <strong className="text-[#f0e6d2]">Riot LoL Esports:</strong> Official tournament rulebooks, Fearless Draft formats, venues, and competitive rulings.
          </div>
          <div>
            <strong className="text-[#f0e6d2]">Dot Esports & Esports.gg:</strong> Fast daily match recaps, patch meta breakdowns, and power rankings.
          </div>
        </div>
      </div>
    </div>
  );
};
