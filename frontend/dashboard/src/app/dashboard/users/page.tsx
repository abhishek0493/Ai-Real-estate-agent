"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { usersApi } from "@/services/api";
import { useAuth } from "@/context/AuthContext";

export default function UsersPage() {
  const { user } = useAuth();
  const router = useRouter();
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ email: "", password: "", role: "AGENT" });

  // Redirect non-admin users
  useEffect(() => {
    if (user && user.role !== "SUPER_ADMIN") router.replace("/dashboard");
  }, [user, router]);

  const { data: users, isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: () => usersApi.list().then((r) => r.data),
    enabled: user?.role === "SUPER_ADMIN",
  });

  const createMut = useMutation({
    mutationFn: (data: { email: string; password: string; role: string }) => usersApi.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["users"] }); setShowForm(false); setForm({ email: "", password: "", role: "AGENT" }); },
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => usersApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });

  if (user?.role !== "SUPER_ADMIN") return null;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Users</h1>
          <p className="text-gray-400 text-sm">Manage your team members</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-xl transition shadow-lg shadow-indigo-500/20"
        >
          {showForm ? "Cancel" : "+ Add User"}
        </button>
      </div>

      {/* Add form */}
      {showForm && (
        <div className="bg-gray-900/60 border border-gray-800 rounded-2xl p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <input placeholder="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="px-4 py-2.5 bg-gray-800/50 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            <input placeholder="Password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="px-4 py-2.5 bg-gray-800/50 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}
              className="px-4 py-2.5 bg-gray-800/50 border border-gray-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-indigo-500">
              <option value="AGENT">Agent</option>
              <option value="SUPER_ADMIN">Super Admin</option>
            </select>
            <button onClick={() => createMut.mutate(form)}
              className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-xl transition">
              Create User
            </button>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="bg-gray-900/60 border border-gray-800 rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-gray-400 text-left">
              <th className="px-6 py-4 font-medium">Email</th>
              <th className="px-6 py-4 font-medium">Role</th>
              <th className="px-6 py-4 font-medium">Status</th>
              <th className="px-6 py-4 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={4} className="px-6 py-8 text-center text-gray-500">Loading…</td></tr>
            ) : users?.length === 0 ? (
              <tr><td colSpan={4} className="px-6 py-8 text-center text-gray-500">No users yet</td></tr>
            ) : (
              users?.map((u) => (
                <tr key={u.id} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition">
                  <td className="px-6 py-4 text-white font-medium">{u.email}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                      u.role === "SUPER_ADMIN" ? "bg-purple-500/10 text-purple-400" : "bg-blue-500/10 text-blue-400"
                    }`}>
                      {u.role}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                      u.is_active ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"
                    }`}>
                      {u.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    {u.id !== user?.id && (
                      <button onClick={() => deleteMut.mutate(u.id)} className="text-red-400 hover:text-red-300 text-xs font-medium transition">
                        Delete
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
