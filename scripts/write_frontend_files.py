"""Write clean frontend assignment files - v2 active/inactive."""
import pathlib

PAGE_CONTENT = '''\
"use client";

import { useState, useEffect, useCallback } from "react";
import { Assignment, AssignmentStatus } from "@/types";
import { assignmentService } from "@/lib/api/assignment.service";
import AssignSurveyModal from "@/components/assignment/assign-survey-modal";
import {
  Plus,
  RefreshCw,
  ClipboardList,
  Users,
  UserCheck,
  Trash2,
  Clock,
  PlayCircle,
  CheckCircle,
  Info,
} from "lucide-react";

interface SurveyGroup {
  surveyId: number;
  surveyTitle: string;
  encargados: Assignment[];
  brigadistas: Assignment[];
}

const STATUS_INFO: Record<
  AssignmentStatus,
  { label: string; Icon: any; className: string; tip: string }
> = {
  pending: {
    label: "Pendiente",
    Icon: Clock,
    className: "bg-yellow-100 text-yellow-700",
    tip: "No iniciada en la app movil todavia.",
  },
  in_progress: {
    label: "En curso",
    Icon: PlayCircle,
    className: "bg-blue-100 text-blue-700",
    tip: "Abierta y en progreso en la app movil.",
  },
  completed: {
    label: "Completada",
    Icon: CheckCircle,
    className: "bg-green-100 text-green-700",
    tip: "Enviada desde la app movil.",
  },
};

function StatusBadge({ status }: { status: AssignmentStatus }) {
  const [showTip, setShowTip] = useState(false);
  const cfg = STATUS_INFO[status] ?? STATUS_INFO.pending;
  const { Icon } = cfg;
  return (
    <span className="relative inline-flex">
      <span
        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium cursor-default ${cfg.className}`}
        onMouseEnter={() => setShowTip(true)}
        onMouseLeave={() => setShowTip(false)}
      >
        <Icon className="h-3 w-3" />
        {cfg.label}
      </span>
      {showTip && (
        <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-52 bg-gray-900 text-white text-xs rounded-lg px-3 py-2 z-50 pointer-events-none leading-relaxed text-center">
          {cfg.tip}
        </span>
      )}
    </span>
  );
}

function AssignedUserCard({
  assignment,
  onDelete,
}: {
  assignment: Assignment;
  onDelete: (id: number) => void;
}) {
  const user = assignment.user;
  const initials = user?.full_name
    ? user.full_name
        .split(" ")
        .map((n) => n[0])
        .slice(0, 2)
        .join("")
        .toUpperCase()
    : "?";
  return (
    <div className="flex items-center justify-between gap-3 bg-white rounded-lg border border-gray-200 px-3 py-2.5 group">
      <div className="flex items-center gap-2.5 min-w-0">
        <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-xs font-bold flex-shrink-0">
          {initials}
        </div>
        <div className="min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">
            {user?.full_name ?? `Usuario #${assignment.user_id}`}
          </p>
          {assignment.location && (
            <p className="text-xs text-gray-400 truncate">
              {assignment.location}
            </p>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        <StatusBadge status={assignment.status} />
        <button
          onClick={() => onDelete(assignment.id)}
          className="p-1 rounded text-gray-300 hover:text-red-500 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition-all"
          title="Quitar asignacion"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}

function SurveyCard({
  group,
  onDelete,
  onAddUser,
}: {
  group: SurveyGroup;
  onDelete: (id: number) => void;
  onAddUser: (surveyId: number, surveyTitle: string) => void;
}) {
  const all = [...group.encargados, ...group.brigadistas];
  const completed = all.filter((a) => a.status === "completed").length;
  return (
    <div className="bg-gray-50 rounded-xl border border-gray-200 overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4 bg-white border-b border-gray-200">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-primary-100 text-primary-700 flex items-center justify-center">
            <ClipboardList className="h-[18px] w-[18px]" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{group.surveyTitle}</h3>
            <p className="text-xs text-gray-500">
              {all.length} asignado{all.length !== 1 ? "s" : ""}
              {all.length > 0 &&
                ` · ${completed} completada${completed !== 1 ? "s" : ""}`}
            </p>
          </div>
        </div>
        <button
          onClick={() => onAddUser(group.surveyId, group.surveyTitle)}
          className="flex items-center gap-1.5 text-sm text-primary-600 hover:text-primary-700 font-medium px-3 py-1.5 rounded-lg hover:bg-primary-50 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Asignar usuario
        </button>
      </div>
      <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2.5">
            <UserCheck className="h-4 w-4 text-indigo-500" />
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Encargados ({group.encargados.length})
            </span>
          </div>
          {group.encargados.length === 0 ? (
            <p className="text-xs text-gray-400 italic px-1">
              Sin encargado asignado
            </p>
          ) : (
            <div className="space-y-1.5">
              {group.encargados.map((a) => (
                <AssignedUserCard key={a.id} assignment={a} onDelete={onDelete} />
              ))}
            </div>
          )}
        </div>
        <div>
          <div className="flex items-center gap-2 mb-2.5">
            <Users className="h-4 w-4 text-purple-500" />
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Brigadistas ({group.brigadistas.length})
            </span>
          </div>
          {group.brigadistas.length === 0 ? (
            <p className="text-xs text-gray-400 italic px-1">
              Sin brigadistas asignados
            </p>
          ) : (
            <div className="space-y-1.5">
              {group.brigadistas.map((a) => (
                <AssignedUserCard key={a.id} assignment={a} onDelete={onDelete} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function AssignmentsPage() {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [preselectedSurvey, setPreselectedSurvey] = useState<{
    id: number;
    title: string;
  } | null>(null);

  const loadAssignments = useCallback(async () => {
    setIsLoading(true);
    try {
      setAssignments(await assignmentService.getAssignments());
    } catch (err) {
      console.error("Error loading assignments:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAssignments();
  }, [loadAssignments]);

  const groups: SurveyGroup[] = Object.values(
    assignments.reduce<Record<number, SurveyGroup>>((acc, a) => {
      const sid = a.survey_id;
      if (!acc[sid]) {
        acc[sid] = {
          surveyId: sid,
          surveyTitle: a.survey?.title ?? `Encuesta #${sid}`,
          encargados: [],
          brigadistas: [],
        };
      }
      if (a.user?.role === "encargado") acc[sid].encargados.push(a);
      else acc[sid].brigadistas.push(a);
      return acc;
    }, {}),
  ).sort((a, b) => a.surveyTitle.localeCompare(b.surveyTitle));

  const stats = {
    surveys: groups.length,
    total: assignments.length,
    pending: assignments.filter((a) => a.status === "pending").length,
    completed: assignments.filter((a) => a.status === "completed").length,
  };

  const openModal = (surveyId?: number, surveyTitle?: string) => {
    setPreselectedSurvey(
      surveyId ? { id: surveyId, title: surveyTitle! } : null,
    );
    setIsModalOpen(true);
  };

  const handleCreate = async (data: {
    user_id: number;
    survey_id: number;
    location?: string;
    notes?: string;
  }) => {
    setIsSaving(true);
    try {
      await assignmentService.createAssignment(data);
      setIsModalOpen(false);
      await loadAssignments();
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Quitar esta asignacion?")) return;
    try {
      await assignmentService.deleteAssignment(id);
      setAssignments((prev) => prev.filter((a) => a.id !== id));
    } catch (err) {
      console.error("Error deleting assignment:", err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Asignaciones</h1>
          <p className="text-gray-500 mt-1">
            Asigna encargados y brigadistas a cada encuesta
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadAssignments}
            disabled={isLoading}
            className="p-2.5 border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-600 transition-colors"
            title="Recargar"
          >
            <RefreshCw
              className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`}
            />
          </button>
          <button
            onClick={() => openModal()}
            className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2.5 rounded-lg hover:bg-primary-700 transition-colors font-medium"
          >
            <Plus className="h-5 w-5" />
            Nueva asignacion
          </button>
        </div>
      </div>

      <div className="flex items-start gap-3 bg-blue-50 border border-blue-200 rounded-lg px-4 py-3">
        <Info className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
        <p className="text-sm text-blue-700">
          Los estados (
          <span className="font-medium">Pendiente · En curso · Completada</span>
          ) los actualiza automaticamente la app movil cuando el usuario llena la
          encuesta. Desde el CMS solo se crean y eliminan asignaciones.
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          {
            label: "Encuestas con asignados",
            value: stats.surveys,
            color: "text-gray-900",
          },
          {
            label: "Personas asignadas",
            value: stats.total,
            color: "text-gray-700",
          },
          {
            label: "Pendientes",
            value: stats.pending,
            color: "text-yellow-600",
          },
          {
            label: "Completadas",
            value: stats.completed,
            color: "text-green-600",
          },
        ].map((s) => (
          <div
            key={s.label}
            className="bg-white rounded-lg border border-gray-200 p-4"
          >
            <p className="text-xs text-gray-500">{s.label}</p>
            <p className={`text-3xl font-bold mt-1 ${s.color}`}>{s.value}</p>
          </div>
        ))}
      </div>

      {isLoading ? (
        <div className="bg-white rounded-xl border border-gray-200 p-16 text-center">
          <div className="animate-spin h-10 w-10 border-4 border-primary-500 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-gray-500">Cargando...</p>
        </div>
      ) : groups.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-16 text-center">
          <ClipboardList className="mx-auto h-14 w-14 text-gray-200 mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-1">
            Sin asignaciones
          </h3>
          <p className="text-gray-500 mb-6 max-w-sm mx-auto">
            Empieza asignando un encargado a una encuesta. Luego agrega los
            brigadistas que la llevaran a cabo.
          </p>
          <button
            onClick={() => openModal()}
            className="inline-flex items-center gap-2 bg-primary-600 text-white px-5 py-2.5 rounded-lg hover:bg-primary-700 transition-colors font-medium"
          >
            <Plus className="h-5 w-5" />
            Crear primera asignacion
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {groups.map((group) => (
            <SurveyCard
              key={group.surveyId}
              group={group}
              onDelete={handleDelete}
              onAddUser={openModal}
            />
          ))}
        </div>
      )}

      <AssignSurveyModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleCreate}
        isLoading={isSaving}
        preselectedSurvey={preselectedSurvey}
      />
    </div>
  );
}
'''

MODAL_CONTENT = '''\
"use client";

import { useState, useEffect } from "react";
import { User, Survey } from "@/types";
import { userService } from "@/lib/api/user.service";
import { surveyService } from "@/lib/api/survey.service";
import {
  X,
  ClipboardList,
  MapPin,
  ChevronDown,
  UserCheck,
  Users,
} from "lucide-react";

interface AssignSurveyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: {
    user_id: number;
    survey_id: number;
    location?: string;
    notes?: string;
  }) => Promise<void>;
  isLoading?: boolean;
  preselectedSurvey?: { id: number; title: string } | null;
}

export default function AssignSurveyModal({
  isOpen,
  onClose,
  onSubmit,
  isLoading = false,
  preselectedSurvey,
}: AssignSurveyModalProps) {
  const [encargados, setEncargados] = useState<User[]>([]);
  const [brigadistas, setBrigadistas] = useState<User[]>([]);
  const [surveys, setSurveys] = useState<Survey[]>([]);
  const [loadingData, setLoadingData] = useState(false);

  const [surveyId, setSurveyId] = useState<number | "">("");
  const [userId, setUserId] = useState<number | "">("");
  const [roleTab, setRoleTab] = useState<"encargado" | "brigadista">("encargado");
  const [location, setLocation] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isOpen) return;
    setUserId("");
    setLocation("");
    setError("");
    setRoleTab("encargado");
    setSurveyId(preselectedSurvey ? preselectedSurvey.id : "");

    const load = async () => {
      setLoadingData(true);
      try {
        const [enc, brig, surveyList] = await Promise.all([
          userService.getUsers({ rol: "encargado", activo: true }),
          userService.getUsers({ rol: "brigadista", activo: true }),
          surveyService.getSurveys({ limit: 200 }),
        ]);
        setEncargados(enc);
        setBrigadistas(brig);
        setSurveys(surveyList.filter((s) => s.is_active));
      } catch {
        setError("Error al cargar datos.");
      } finally {
        setLoadingData(false);
      }
    };
    load();
  }, [isOpen, preselectedSurvey]);

  const activeUsers = roleTab === "encargado" ? encargados : brigadistas;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!surveyId || !userId) {
      setError("Selecciona una encuesta y un usuario.");
      return;
    }
    setError("");
    try {
      await onSubmit({
        survey_id: Number(surveyId),
        user_id: Number(userId),
        location: location.trim() || undefined,
      });
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? "Error al crear asignacion.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl max-w-md w-full shadow-xl">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-bold text-gray-900">Nueva asignacion</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100"
            disabled={isLoading}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          {loadingData ? (
            <div className="py-8 text-center text-gray-500">
              <div className="animate-spin h-7 w-7 border-4 border-primary-500 border-t-transparent rounded-full mx-auto mb-3" />
              Cargando...
            </div>
          ) : (
            <>
              {/* Step 1 */}
              <div>
                <label className="flex items-center gap-1.5 text-sm font-semibold text-gray-700 mb-1.5">
                  <span className="w-5 h-5 rounded-full bg-primary-600 text-white text-xs flex items-center justify-center font-bold">
                    1
                  </span>
                  Encuesta
                </label>
                {preselectedSurvey ? (
                  <div className="flex items-center gap-2 px-3 py-2.5 bg-primary-50 border border-primary-200 rounded-lg">
                    <ClipboardList className="h-4 w-4 text-primary-500 flex-shrink-0" />
                    <span className="text-sm font-medium text-primary-800">
                      {preselectedSurvey.title}
                    </span>
                  </div>
                ) : (
                  <div className="relative">
                    <select
                      value={surveyId}
                      onChange={(e) =>
                        setSurveyId(e.target.value ? Number(e.target.value) : "")
                      }
                      className="w-full pl-3 pr-10 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white appearance-none"
                      required
                      disabled={isLoading}
                    >
                      <option value="">Seleccionar encuesta...</option>
                      {surveys.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.title}
                        </option>
                      ))}
                    </select>
                    <ChevronDown className="absolute right-3 top-3 h-4 w-4 text-gray-400 pointer-events-none" />
                  </div>
                )}
              </div>

              {/* Step 2 */}
              <div>
                <label className="flex items-center gap-1.5 text-sm font-semibold text-gray-700 mb-2">
                  <span className="w-5 h-5 rounded-full bg-primary-600 text-white text-xs flex items-center justify-center font-bold">
                    2
                  </span>
                  A quien asignas?
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => { setRoleTab("encargado"); setUserId(""); }}
                    className={`flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg border text-sm font-medium transition-colors ${
                      roleTab === "encargado"
                        ? "bg-indigo-50 border-indigo-300 text-indigo-700"
                        : "bg-white border-gray-300 text-gray-600 hover:bg-gray-50"
                    }`}
                  >
                    <UserCheck className="h-4 w-4" />
                    Encargado
                  </button>
                  <button
                    type="button"
                    onClick={() => { setRoleTab("brigadista"); setUserId(""); }}
                    className={`flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg border text-sm font-medium transition-colors ${
                      roleTab === "brigadista"
                        ? "bg-purple-50 border-purple-300 text-purple-700"
                        : "bg-white border-gray-300 text-gray-600 hover:bg-gray-50"
                    }`}
                  >
                    <Users className="h-4 w-4" />
                    Brigadista
                  </button>
                </div>
                <p className="text-xs text-gray-400 mt-1.5">
                  {roleTab === "encargado"
                    ? "El encargado supervisa y coordina esta encuesta."
                    : "El brigadista la aplica en campo."}
                </p>
              </div>

              {/* Step 3 */}
              <div>
                <label className="flex items-center gap-1.5 text-sm font-semibold text-gray-700 mb-1.5">
                  <span className="w-5 h-5 rounded-full bg-primary-600 text-white text-xs flex items-center justify-center font-bold">
                    3
                  </span>
                  {roleTab === "encargado" ? "Seleccionar encargado" : "Seleccionar brigadista"}
                </label>
                <div className="relative">
                  <select
                    value={userId}
                    onChange={(e) =>
                      setUserId(e.target.value ? Number(e.target.value) : "")
                    }
                    className="w-full pl-3 pr-10 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white appearance-none"
                    required
                    disabled={isLoading}
                  >
                    <option value="">
                      {roleTab === "encargado"
                        ? "Seleccionar encargado..."
                        : "Seleccionar brigadista..."}
                    </option>
                    {activeUsers.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.nombre} {u.apellido}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-3 top-3 h-4 w-4 text-gray-400 pointer-events-none" />
                </div>
                {activeUsers.length === 0 && (
                  <p className="text-xs text-amber-600 mt-1">
                    No hay{" "}
                    {roleTab === "encargado" ? "encargados" : "brigadistas"}{" "}
                    activos.
                  </p>
                )}
              </div>

              {/* Zona */}
              <div>
                <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1">
                  <MapPin className="h-4 w-4 text-gray-400" />
                  Zona / Sector
                  <span className="text-gray-400 font-normal ml-1">(opcional)</span>
                </label>
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="Ej: Colonia Centro, Sector Norte"
                  className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  disabled={isLoading}
                />
              </div>
            </>
          )}
        </form>

        <div className="flex justify-end gap-3 px-6 pb-6">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            disabled={isLoading}
          >
            Cancelar
          </button>
          <button
            onClick={handleSubmit}
            className="px-4 py-2 text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
            disabled={isLoading || loadingData || !surveyId || !userId}
          >
            {isLoading ? "Asignando..." : "Asignar"}
          </button>
        </div>
      </div>
    </div>
  );
}
'''

page_path = pathlib.Path("/Users/dou1013/Documents/GithubProyects/brigadaWebCMS/src/app/dashboard/assignments/page.tsx")
modal_path = pathlib.Path("/Users/dou1013/Documents/GithubProyects/brigadaWebCMS/src/components/assignment/assign-survey-modal.tsx")

page_path.write_text(PAGE_CONTENT, encoding="utf-8")
print(f"Wrote page: {page_path} ({page_path.stat().st_size} bytes)")

modal_path.write_text(MODAL_CONTENT, encoding="utf-8")
print(f"Wrote modal: {modal_path} ({modal_path.stat().st_size} bytes)")
