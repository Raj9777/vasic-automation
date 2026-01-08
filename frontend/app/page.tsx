"use client";
import { useState } from 'react';
import axios from 'axios';

export default function Home() {
  const [activeTab, setActiveTab] = useState('single');
  const [url, setUrl] = useState('');
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');

  const handleScrape = async (endpoint) => {
    if (!url) return;
    setLoading(true);
    setStatus(endpoint === 'deep-search' ? 'Performing Deep Intelligence Search (Google/LinkedIn)...' : 'Scanning website...');
    setLeads([]);

    try {
      // Use the correct endpoint based on button click
      const apiPath = endpoint === 'deep-search' ? '/deep-search' : '/scrape';
      const response = await axios.post(`https://vasic-backend.onrender.com${apiPath}`, { url });
      
      setLeads(response.data.leads);
      if (response.data.leads.length > 0) {
        setStatus(`Success! Found ${response.data.leads.length} leads.`);
      } else {
        setStatus('No emails found.');
      }
    } catch (error) {
      setStatus('Error: Scan failed.');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center p-8 font-sans">
      <h1 className="text-5xl font-extrabold mb-2 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">
        Vasic Automation
      </h1>
      <p className="mb-8 text-gray-400 text-lg">AI-Powered Decision Maker Verification</p>

      {/* TABS */}
      <div className="flex space-x-2 mb-8 bg-gray-800 p-1 rounded-lg">
        <button onClick={() => setActiveTab('single')} className={`px-4 py-2 rounded-md font-bold transition ${activeTab === 'single' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}>
          Fast Scan (Free)
        </button>
        <button onClick={() => setActiveTab('deep')} className={`px-4 py-2 rounded-md font-bold transition ${activeTab === 'deep' ? 'bg-indigo-600 text-white shadow-lg border border-indigo-400' : 'text-gray-400 hover:text-white'}`}>
          Deep Search (Beta)
        </button>
        <button onClick={() => setActiveTab('bulk')} className={`px-4 py-2 rounded-md font-bold transition flex items-center ${activeTab === 'bulk' ? 'bg-purple-600 text-white' : 'text-gray-400 hover:text-white'}`}>
          Bulk Scan <span className="ml-2 text-xs bg-yellow-500 text-black px-1 rounded">PRO</span>
        </button>
      </div>

      {/* SINGLE & DEEP SEARCH SHARE SAME UI */}
      {(activeTab === 'single' || activeTab === 'deep') && (
        <div className="w-full max-w-2xl bg-gray-800 p-8 rounded-2xl shadow-2xl border border-gray-700">
          <label className="block text-sm font-bold mb-3 text-gray-300">Target Company URL</label>
          <div className="flex space-x-2 mb-6">
            <input
              type="text"
              className="flex-1 p-4 rounded-xl bg-gray-700 border border-gray-600 focus:outline-none focus:border-blue-500 text-lg"
              placeholder="example.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
            <button
              onClick={() => handleScrape(activeTab === 'deep' ? 'deep-search' : 'scrape')}
              disabled={loading}
              className={`px-8 rounded-xl font-bold text-lg transition ${
                loading ? 'bg-gray-600 cursor-not-allowed' : activeTab === 'deep' ? 'bg-indigo-600 hover:bg-indigo-500' : 'bg-blue-600 hover:bg-blue-500'
              }`}
            >
              {loading ? 'Thinking...' : activeTab === 'deep' ? 'Deep Search' : 'Scan'}
            </button>
          </div>

          {status && <p className="mb-4 text-center text-sm text-yellow-400 animate-pulse">{status}</p>}

          {leads.length > 0 && (
            <div className="bg-gray-900 rounded-xl border border-gray-700 overflow-hidden">
              {leads.map((lead, index) => (
                <div key={index} className="p-4 border-b border-gray-800 last:border-0 flex justify-between items-center hover:bg-gray-800/50">
                  <div className="flex flex-col">
                    <span className="font-mono text-white text-base">{lead.email}</span>
                    <span className="text-xs text-gray-500">{lead.source}</span>
                  </div>
                  <span className="text-xs px-2 py-1 rounded bg-gray-700 text-gray-300 border border-gray-600">
                    {lead.confidence}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* BULK TAB (Locked) */}
      {activeTab === 'bulk' && (
        <div className="w-full max-w-2xl bg-gray-800 p-12 rounded-2xl text-center border border-purple-500/30">
          <h2 className="text-3xl font-bold mb-4">Bulk Engine ⚡</h2>
          <p className="text-gray-400 mb-8">Process 500 URLs at once.</p>
          <button className="bg-purple-600 px-8 py-4 rounded-xl font-bold text-lg">Get Pro ($29/mo)</button>
        </div>
      )}
    </div>
  );
}
