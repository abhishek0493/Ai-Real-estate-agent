"use client";

import { useQuery } from "@tanstack/react-query";
import { leadsApi, propertiesApi, usersApi } from "@/services/api";
import { useAuth } from "@/context/AuthContext";

function StatCard({ label, value, icon, color }: { label: string; value: string | number; icon: string; color: string }) {
  return (
    <div className="bg-gray-900/60 backdrop-blur-xl border border-gray-800 rounded-2xl p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-400">{label}</p>
          <p className="text-3xl font-bold text-white mt-1">{value}</p>
        </div>
        <div className={`w-12 h-12 rounded-xl ${color} flex items-center justify-center`}>
          <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={icon} />
          </svg>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const { data: leads } = useQuery({ queryKey: ["leads"], queryFn: () => leadsApi.list().then((r) => r.data) });
  const { data: properties } = useQuery({ queryKey: ["properties"], queryFn: () => propertiesApi.list().then((r) => r.data) });
  const { data: users } = useQuery({
    queryKey: ["users"],
    queryFn: () => usersApi.list().then((r) => r.data),
    enabled: user?.role === "SUPER_ADMIN",
  });

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-1">Dashboard</h1>
      <p className="text-gray-400 mb-8">Welcome back, {user?.email}</p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          label="Total Leads"
          value={leads?.length ?? "—"}
          icon="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"
          color="bg-indigo-600/20"
        />
        <StatCard
          label="Properties"
          value={properties?.length ?? "—"}
          icon="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
          color="bg-emerald-600/20"
        />
        <StatCard
          label="Active Leads"
          value={leads?.filter((l) => l.status !== "CLOSED").length ?? "—"}
          icon="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
          color="bg-amber-600/20"
        />
        {user?.role === "SUPER_ADMIN" && (
          <StatCard
            label="Team Members"
            value={users?.length ?? "—"}
            icon="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197"
            color="bg-purple-600/20"
          />
        )}
      </div>
    </div>
  );
}
