"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { propertiesApi, PropertyCreate } from "@/services/api";
import { useAuth } from "@/context/AuthContext";

export default function PropertiesPage() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const isAdmin = user?.role === "SUPER_ADMIN";
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<PropertyCreate>({
    location: "", price: 0, bedrooms: 2, bathrooms: 1, square_feet: 800, available: true,
  });

  const { data: properties, isLoading } = useQuery({
    queryKey: ["properties"],
    queryFn: () => propertiesApi.list().then((r) => r.data),
  });

  const createMut = useMutation({
    mutationFn: (data: PropertyCreate) => propertiesApi.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["properties"] }); setShowForm(false); },
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => propertiesApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["properties"] }),
  });

  const formatPrice = (p: number) => `₹${(p / 100000).toFixed(1)}L`;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Properties</h1>
          <p className="text-gray-400 text-sm">Manage your property listings</p>
        </div>
        {isAdmin && (
          <button
            onClick={() => setShowForm(!showForm)}
            className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-xl transition shadow-lg shadow-indigo-500/20"
          >
            {showForm ? "Cancel" : "+ Add Property"}
          </button>
        )}
      </div>

      {/* Add form */}
      {showForm && (
        <div className="bg-gray-900/60 border border-gray-800 rounded-2xl p-6 mb-6">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="prop-location" className="block text-sm font-medium text-gray-300 mb-1.5">Location</label>
              <input id="prop-location" placeholder="e.g. Andheri West" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })}
                className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
            <div>
              <label htmlFor="prop-price" className="block text-sm font-medium text-gray-300 mb-1.5">Price (₹)</label>
              <input id="prop-price" placeholder="e.g. 8500000" type="number" value={form.price || ""} onChange={(e) => setForm({ ...form, price: +e.target.value })}
                className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
            <div>
              <label htmlFor="prop-bedrooms" className="block text-sm font-medium text-gray-300 mb-1.5">Bedrooms</label>
              <input id="prop-bedrooms" placeholder="2" type="number" value={form.bedrooms} onChange={(e) => setForm({ ...form, bedrooms: +e.target.value })}
                className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
            <div>
              <label htmlFor="prop-bathrooms" className="block text-sm font-medium text-gray-300 mb-1.5">Bathrooms</label>
              <input id="prop-bathrooms" placeholder="1" type="number" value={form.bathrooms} onChange={(e) => setForm({ ...form, bathrooms: +e.target.value })}
                className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
            <div>
              <label htmlFor="prop-sqft" className="block text-sm font-medium text-gray-300 mb-1.5">Square Feet</label>
              <input id="prop-sqft" placeholder="850" type="number" value={form.square_feet} onChange={(e) => setForm({ ...form, square_feet: +e.target.value })}
                className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
            <div className="flex items-end">
              <button onClick={() => createMut.mutate(form)}
                className="w-full px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-xl transition">
                Save Property
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="bg-gray-900/60 border border-gray-800 rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-gray-400 text-left">
              <th className="px-6 py-4 font-medium">Location</th>
              <th className="px-6 py-4 font-medium">Price</th>
              <th className="px-6 py-4 font-medium">Bedrooms</th>
              <th className="px-6 py-4 font-medium">Available</th>
              {isAdmin && <th className="px-6 py-4 font-medium">Actions</th>}
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={5} className="px-6 py-8 text-center text-gray-500">Loading…</td></tr>
            ) : properties?.length === 0 ? (
              <tr><td colSpan={5} className="px-6 py-8 text-center text-gray-500">No properties yet</td></tr>
            ) : (
              properties?.map((p) => (
                <tr key={p.id} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition">
                  <td className="px-6 py-4 text-white font-medium">{p.location}</td>
                  <td className="px-6 py-4 text-emerald-400">{formatPrice(p.price)}</td>
                  <td className="px-6 py-4 text-gray-300">{p.bedrooms} BHK</td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${p.available ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"}`}>
                      {p.available ? "Available" : "Sold"}
                    </span>
                  </td>
                  {isAdmin && (
                    <td className="px-6 py-4">
                      <button onClick={() => deleteMut.mutate(p.id)} className="text-red-400 hover:text-red-300 text-xs font-medium transition">
                        Delete
                      </button>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
