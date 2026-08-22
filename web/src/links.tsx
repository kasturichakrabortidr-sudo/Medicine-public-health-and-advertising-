import { createContext, useContext, type MouseEvent, type ReactNode } from "react";
import type { ReferenceItem } from "./types";

export type LinkableRef = {
  n?: number | null;
  ref?: number | null;
  url?: string;
  pmid?: string;
  doi?: string;
};

const RefCtx = createContext<ReferenceItem[]>([]);

export function RefLinksProvider({
  refs,
  children,
}: {
  refs: ReferenceItem[];
  children: ReactNode;
}) {
  return <RefCtx.Provider value={refs || []}>{children}</RefCtx.Provider>;
}

export function useRefLinks(): ReferenceItem[] {
  return useContext(RefCtx);
}

export function paperHref(row?: LinkableRef | null): string {
  if (!row) return "";
  const url = (row.url || "").trim();
  if (/^https?:\/\//i.test(url)) return url;
  if (url.startsWith("//")) return `https:${url}`;
  const pmid = String(row.pmid || "").replace(/\D/g, "");
  if (pmid) return `https://pubmed.ncbi.nlm.nih.gov/${pmid}/`;
  const doi = String(row.doi || "")
    .trim()
    .replace(/^doi:\s*/i, "");
  if (doi) return `https://doi.org/${doi}`;
  if (row.n) return `#ref-${row.n}`;
  if (row.ref) return `#ref-${row.ref}`;
  return url;
}

export function openPaper(href: string, event?: MouseEvent<HTMLAnchorElement>) {
  if (!href) return;
  if (href.startsWith("#")) {
    event?.preventDefault();
    document.getElementById(href.slice(1))?.scrollIntoView({ behavior: "smooth", block: "center" });
    return;
  }
  event?.preventDefault();
  const opened = window.open(href, "_blank", "noopener,noreferrer");
  if (opened) {
    try {
      opened.opener = null;
    } catch {
      /* ignore */
    }
    return;
  }
  window.location.assign(href);
}

export function PaperAnchor({
  href,
  children,
  className,
}: {
  href?: string;
  children: ReactNode;
  className?: string;
}) {
  const resolved = href || "";
  if (!resolved) return <>{children}</>;
  return (
    <a
      className={className || "paper-link"}
      href={resolved}
      target={resolved.startsWith("#") ? undefined : "_blank"}
      rel="noopener noreferrer"
      onClick={(event) => openPaper(resolved, event)}
    >
      {children}
    </a>
  );
}
