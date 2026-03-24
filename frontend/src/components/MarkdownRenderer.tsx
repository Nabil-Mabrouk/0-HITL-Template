import ReactMarkdown   from "react-markdown";
import remarkGfm        from "remark-gfm";
import rehypeHighlight  from "rehype-highlight";
import rehypeRaw        from "rehype-raw";
import "highlight.js/styles/github-dark.css";

//const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

interface Props {
  content: string;
}

export default function MarkdownRenderer({ content }: Props) {

  // Pré-traitement : convertir [video:URL] et [audio:URL] en balises HTML
  const processed = content
    .replace(
      /\[video:(.*?)\]/g,
      (_, url) =>
        `<video controls class="w-full rounded-xl border border-white/10 my-4" src="${url}"></video>`
    )
    .replace(
      /\[audio:(.*?)\]/g,
      (_, url) =>
        `<audio controls class="w-full my-4" src="${url}"></audio>`
    );

  return (
    <div className="prose prose-invert max-w-none
                    prose-headings:font-bold prose-headings:text-white
                    prose-p:text-white/80 prose-p:leading-relaxed
                    prose-a:text-indigo-400 prose-a:no-underline
                    hover:prose-a:underline
                    prose-code:text-indigo-300 prose-code:bg-white/5
                    prose-code:px-1 prose-code:rounded
                    prose-pre:bg-zinc-900 prose-pre:border
                    prose-pre:border-white/10 prose-pre:rounded-xl
                    prose-blockquote:border-l-indigo-500
                    prose-blockquote:text-white/60
                    prose-img:rounded-xl prose-img:border
                    prose-img:border-white/10
                    prose-table:text-sm
                    prose-th:text-white prose-td:text-white/70">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight, rehypeRaw]}
        children={processed}
        components={{
          a({ href, children, ...props }) {
            if (!href) return <a href={href} {...props}>{children}</a>;

            // Embed YouTube
            const ytMatch = href.match(
              /(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\s]+)/
            );
            if (ytMatch) {
              return (
                <div className="my-6 aspect-video rounded-xl overflow-hidden
                                border border-white/10">
                  <iframe
                    src={`https://www.youtube.com/embed/${ytMatch[1]}`}
                    className="w-full h-full"
                    allowFullScreen
                    title="Vidéo YouTube"
                  />
                </div>
              );
            }

            return <a href={href} {...props}>{children}</a>;
          },
        }}
      />
    </div>
  );
}
