import React, { useState, useEffect } from 'react';
import { mobileApi } from '../../services/api';
import {
  ShieldCheck, Users, Plus, QrCode, FileText, Check, Clock, Upload, X
} from 'lucide-react';

export default function EmployeeScreen({ lang }) {
  const [profile, setProfile] = useState(null);
  const [showAddFamily, setShowAddFamily] = useState(false);
  const [showApplyPass, setShowApplyPass] = useState(false);
  const [viewingPass, setViewingPass] = useState(null);

  // New family form
  const [fullName, setFullName] = useState('');
  const [relationType, setRelationType] = useState('spouse');
  const [dob, setDob] = useState('1990-05-15');
  const [idNumber, setIdNumber] = useState('998811223344');

  // Apply form
  const [selectedFamilyMemberId, setSelectedFamilyMemberId] = useState('');

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const data = await mobileApi.getPassProfile();
      setProfile(data);
      if (data.family_members && data.family_members.length > 0) {
        setSelectedFamilyMemberId(data.family_members[0].id);
      }
    } catch (e) {}
  };

  const handleAddFamilyMember = async () => {
    if (!fullName) return;
    try {
      await mobileApi.addFamilyMember({
        full_name: fullName,
        relation_type: relationType,
        date_of_birth: dob,
        id_proof_number: idNumber
      });
      setShowAddFamily(false);
      setFullName('');
      fetchProfile();
      alert('Family member registered successfully under employee quota!');
    } catch (e) {
      alert(e.message);
    }
  };

  const handleApplyPass = async () => {
    try {
      await mobileApi.applyPass({
        family_member_id: selectedFamilyMemberId || null,
        pass_type: selectedFamilyMemberId ? 'family' : 'employee',
        academic_year: '2026-2027'
      });
      setShowApplyPass(false);
      fetchProfile();
      alert('Transit pass application submitted for Depot scrutiny!');
    } catch (e) {
      alert(e.message);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
      {/* Employee Profile Header */}
      <div className="mobile-card p-4 space-y-3 bg-gradient-to-br from-slate-900 to-indigo-950/40 border-indigo-500/40">
        <div className="flex justify-between items-start">
          <div>
            <span className="text-[10px] text-indigo-400 font-bold uppercase tracking-wider">
              {lang === 'ta' ? 'ஊழியர் பணி விவரம்' : 'VERIFIED EMPLOYEE PROFILE'}
            </span>
            <h3 className="font-extrabold text-base text-white mt-0.5">
              {profile?.employee_code || 'TNSTC-EMP-1001'}
            </h3>
            <span className="text-[11px] text-slate-300">
              {profile?.designation || 'Senior Transport Specialist'}
            </span>
          </div>
          <span className="badge-active px-2.5 py-1 rounded-full text-[10px] font-bold">
            ELIGIBLE (4 PASSES)
          </span>
        </div>

        <div className="p-2.5 bg-slate-950 rounded-lg text-[11px] text-slate-300 grid grid-cols-2 gap-2">
          <div>
            <span className="text-[10px] text-slate-500 block uppercase">Joined:</span>
            <strong>{profile?.date_of_joining || '2018-04-15'}</strong>
          </div>
          <div>
            <span className="text-[10px] text-slate-500 block uppercase">Pass Quota:</span>
            <strong className="text-emerald-400 font-mono">Up to 4 Dependents</strong>
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setShowAddFamily(true)}
            className="flex-1 py-2 bg-slate-900 border border-slate-700 hover:border-emerald-400 text-slate-200 rounded-lg font-bold text-xs flex items-center justify-center gap-1.5"
          >
            <Plus className="h-3.5 w-3.5 text-emerald-400" />
            <span>Add Family Member</span>
          </button>
          <button
            onClick={() => setShowApplyPass(true)}
            className="flex-1 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-bold text-xs shadow-md shadow-indigo-600/30"
          >
            Apply for Pass
          </button>
        </div>
      </div>

      {/* Active Passes Section */}
      <div className="space-y-2">
        <h4 className="font-bold text-xs text-slate-300 flex items-center gap-1.5">
          <ShieldCheck className="h-4 w-4 text-emerald-400" />
          <span>Issued Cryptographic Transit Passes</span>
        </h4>

        {profile?.active_passes?.length === 0 ? (
          <div className="mobile-card p-4 text-center text-slate-400 text-xs">
            No issued passes yet. Submit application above.
          </div>
        ) : (
          profile?.active_passes?.map((p) => (
            <div key={p.pass_id} className="mobile-card p-3 space-y-2 text-xs">
              <div className="flex justify-between items-start">
                <div>
                  <span className="font-mono text-emerald-400 font-bold">{p.pass_number}</span>
                  <h5 className="font-bold text-white text-xs mt-0.5">{p.holder_name}</h5>
                  <span className="text-[10px] text-slate-400 capitalize">Relationship: {p.holder_type}</span>
                </div>
                <span className="badge-active px-2 py-0.5 rounded text-[10px] font-bold">
                  {p.status.toUpperCase()}
                </span>
              </div>
              <div className="flex justify-between items-center text-[10px] text-slate-400 pt-1 border-t border-slate-800">
                <span>Valid Until: <strong className="text-white">{p.valid_until}</strong></span>
                <button
                  onClick={() => setViewingPass(p)}
                  className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-bold flex items-center gap-1"
                >
                  <QrCode className="h-3 w-3" /> View Pass QR
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Registered Family Members */}
      <div className="space-y-2">
        <h4 className="font-bold text-xs text-slate-300 flex items-center gap-1.5">
          <Users className="h-4 w-4 text-cyan-400" />
          <span>Registered Family Dependents</span>
        </h4>
        <div className="space-y-1.5">
          {profile?.family_members?.map((f) => (
            <div key={f.id} className="p-2.5 bg-slate-900 rounded-lg flex justify-between items-center text-xs">
              <div>
                <strong className="text-white block">{f.full_name}</strong>
                <span className="text-[10px] text-slate-400 capitalize">{f.relation_type}</span>
              </div>
              <span className="text-[10px] text-emerald-400 font-semibold">Eligible</span>
            </div>
          ))}
        </div>
      </div>

      {/* Add Family Member Modal */}
      {showAddFamily && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
          <div className="mobile-card p-5 bg-slate-900 max-w-xs w-full space-y-3 text-xs border-emerald-500">
            <div className="flex justify-between items-center">
              <h4 className="font-bold text-white text-sm">Add Family Dependent</h4>
              <button onClick={() => setShowAddFamily(false)} className="text-slate-400"><X className="h-4 w-4" /></button>
            </div>
            <div className="space-y-2">
              <div>
                <label className="text-[10px] text-slate-400 block mb-0.5">Full Name:</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-xs text-white"
                />
              </div>
              <div>
                <label className="text-[10px] text-slate-400 block mb-0.5">Relationship:</label>
                <select
                  value={relationType}
                  onChange={(e) => setRelationType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-xs text-white"
                >
                  <option value="spouse">Spouse</option>
                  <option value="child">Child</option>
                  <option value="parent">Parent</option>
                </select>
              </div>
              <div>
                <label className="text-[10px] text-slate-400 block mb-0.5">Aadhaar / ID Number:</label>
                <input
                  type="text"
                  value={idNumber}
                  onChange={(e) => setIdNumber(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-xs text-white font-mono"
                />
              </div>
              <button
                onClick={handleAddFamilyMember}
                className="w-full mt-2 py-2.5 bg-emerald-600 text-white font-bold rounded-lg text-xs"
              >
                Save Family Dependent
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Pass QR Viewer Modal */}
      {viewingPass && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
          <div className="mobile-card p-5 bg-slate-900 max-w-xs w-full space-y-3 text-center border-emerald-500">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-emerald-400">Official TNSTC Transit Pass</span>
              <button onClick={() => setViewingPass(null)} className="text-slate-400"><X className="h-4 w-4" /></button>
            </div>
            <div className="p-4 bg-white rounded-xl inline-block mx-auto shadow-2xl">
              <QrCode className="h-28 w-28 text-slate-900 mx-auto" />
              <span className="text-[8px] font-mono font-bold uppercase block mt-1 text-slate-900">
                STATE TRANSIT ENCRYPTED QR
              </span>
            </div>
            <div className="text-[11px] font-mono text-slate-300">
              <div className="font-bold text-white">{viewingPass.holder_name}</div>
              <div className="text-[10px] text-slate-400">Pass No: {viewingPass.pass_number}</div>
              <div className="text-[10px] text-emerald-400 font-bold mt-1">Unlimited Statewide Transit Authorized</div>
            </div>
          </div>
        </div>
      )}

      {/* Apply Pass Modal */}
      {showApplyPass && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
          <div className="mobile-card p-5 bg-slate-900 max-w-xs w-full space-y-3 text-xs border-indigo-500">
            <div className="flex justify-between items-center">
              <h4 className="font-bold text-white text-sm">Apply for Transit Pass</h4>
              <button onClick={() => setShowApplyPass(false)} className="text-slate-400"><X className="h-4 w-4" /></button>
            </div>
            <div className="space-y-2">
              <div>
                <label className="text-[10px] text-slate-400 block mb-0.5">Select Beneficiary:</label>
                <select
                  value={selectedFamilyMemberId}
                  onChange={(e) => setSelectedFamilyMemberId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-xs text-white"
                >
                  <option value="">Self (Employee Pass)</option>
                  {profile?.family_members?.map((f) => (
                    <option key={f.id} value={f.id}>{f.full_name} ({f.relation_type})</option>
                  ))}
                </select>
              </div>
              <div className="p-2.5 bg-slate-950 rounded border border-slate-800 text-[10px] text-slate-400">
                Identity documents will be verified by your designated Depot Manager before State Admin QR generation.
              </div>
              <button
                onClick={handleApplyPass}
                className="w-full mt-2 py-2.5 bg-indigo-600 text-white font-bold rounded-lg text-xs"
              >
                Submit Application
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
