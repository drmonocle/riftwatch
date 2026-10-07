import React, { useEffect, useState } from "react";
import { NewsItem } from "../../types";
import { fetchCuratedNews } from "../../api";
import { Newspaper, ExternalLink, Tag } from "lucide-react";

interface NewsViewProps {
  onOpenUrl: (url: string) => void;
}

export const NewsView: React.FC<NewsViewProps> = ({ onOpenUrl }) => {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCuratedNews().then((data) => {
      setNews(data);
      setLoading(false);
    });
  }, []);

  return (
    <div className="p-4 space-y-4 max-w-4xl mx-auto overflow-y-auto h-full select-none">
      <div className="pb-1 border-b border-[#1e282d] flex items-center justify-between">
        <h2 className="text-xs font-bold text-[#c8aa6e] uppercase tracking-wider">
          LoL Esports Dispatch & Meta Intel
        </h2>
        <span className="text-[10px] text-[#7e8e9f]">Official Riot & Pro Intel</span>
      </div>

      {loading ? (
        <div className="text-center py-12 text-[#7e8e9f] text-xs">Loading pro dispatch…</div>
      ) : (
        <div className="grid gap-3">
          {news.map((item) => (
            <div
              key={item.id}
              onClick={() => onOpenUrl(item.url)}
              className="bg-[#0a1420] border border-[#1e282d] hover:border-[#c8aa6e] p-4 rounded-lg cursor-pointer transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <span className="text-[10px] font-bold text-[#0ac8b9] uppercase tracking-wide flex items-center gap-1">
                    <Tag className="w-3 h-3" />
                    {item.tag}
                  </span>
                  <span className="text-[10px] text-[#7e8e9f]">{item.date}</span>
                </div>

                <h3 className="text-sm font-bold text-[#f0e6d2] mb-1.5 hover:text-[#c8aa6e] transition-colors">
                  {item.title}
                </h3>
                <p className="text-xs text-[#7e8e9f] leading-relaxed mb-3">{item.summary}</p>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-[#1e282d]/50 text-[10px] text-[#7e8e9f]">
                <span>Source: {item.source}</span>
                <span className="flex items-center gap-1 text-[#0ac8b9] hover:underline">
                  Read full breakdown <ExternalLink className="w-3 h-3" />
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
