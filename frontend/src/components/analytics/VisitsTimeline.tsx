import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from "recharts";

interface Props {
  data: { date: string; visits: number }[];
}

export default function VisitsTimeline({ data }: Props) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
        <defs>
          <linearGradient id="visitsGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#6366f1" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
        <XAxis
          dataKey="date"
          tick={{ fill: "#ffffff40", fontSize: 11 }}
          tickFormatter={d => d.slice(5)}  // Afficher MM-DD
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: "#ffffff40", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={30}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "#18181b",
            border: "1px solid #ffffff20",
            borderRadius: "8px",
            color: "#ffffff",
          }}
          labelFormatter={l => `Date : ${l}`}
          formatter={(v) => [`${String(v)} visites`, ""]}
        />
        <Area
          type="monotone"
          dataKey="visits"
          stroke="#6366f1"
          strokeWidth={2}
          fill="url(#visitsGradient)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}