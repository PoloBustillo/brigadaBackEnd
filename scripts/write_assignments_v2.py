"""Write assignments page v2 - active/inactive status + response_count."""
import pathlib

PAGE_CONTENT = """
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
  CheckCircle2,
  XCircle,
  ChevronDown,
  FileText,
  Info,
  ToggleLeft,
  ToggleRight,
} from "lucide-react";

interface SurveyGroup {
  surveyId: number;
  surveyTitle: string;
  encargados: Assignment[];
  brigadistas: Assignment[];
}

function StatusBadge({ status }: { status: AssignmentStatus }) {
  const [showTip, setShowTip] = useState(false);
  const isActive = status === "active";
  return (
    <span className="relative inline-flex">
      <span
        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium cursor-help select-none transition-colors ${
          isActive
            ? "bg-green-100 text-green-700"
            : "bg-gray-100 text-gray-500"
        }`}
        onMouseEnter={() => setShowTip(true)}
        onMouseLeave={() => setShowTip(false)}
      >
        {isActive ? (
          <CheckCircle2 className="h-3 w-3" />
        ) : (
          <XCircle className="h-3 w-3" />
        )}
        {isActive ? "Activo" : "Inactivo"}
      </span>
      {showTip && (
        <span className="absolute bottom-full right-0 mb-2 w-60 bg-gray-900 text-white text-xs rounded-xl px-3.5 py-3 z-50 pointer-events-none shadow-xl">
          <span className="block font-semibold mb-1">
            {isActive ? "Asignacion activa" : "Asignacion inactiva"}
          </span>
          <span className="block text-gray-300 leading-relaxed">
            {isActive
              ? "El usuario puede ver y llenar esta encuesta en la app movil."
              : "El usuario ya no puede acceder a esta encuesta. Sus respuestas previas se conservan."}
          </span>
        </span>
      )}
    </span>
  );
}

function ResponseCountBadge({ count }: { count: number }) {
  if (count === 0)
    return (
      <span className="inline-flex items-center gap-1 text-xs text-gray-400">
        <FileText className="h-3 w-3" />
        Sin respuestas
      </span>
    );
  return (
    <span className="inline-flex items-center gap-1 text-xs text-indigo-600 font-medium">
      <FileText className="h-3 w-3" />
      {count} {count === 1 ? "respuesta" : "respuestas"}
    </span>
  );
}

function AssignedUserCard({
  assignment,
  onDelete,
  onToggleStatus,
}: {
  assignment: Assignment;
  onDelete: (id: number) => void;
  onToggleStatus: (id: number, current: AssignmentStatus) => void;
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
  const isActive = assignment.status === "active";
  return (
    <div
      className={`flex items-center justify-between gap-3 rounded-lg border px-3 py-2.5 group transition-colors ${
        isActive
          ? "bg-white border-gray-200"
          : "bg-gray-50 border-gray-200 opacity-60"
      }`}
    >
      <div className="flex items-center gap-2.5 min-w-0">
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
            isActive
              ? "bg-primary-100 text-primary-700"
              : "bg-gray-200 text-gray-500"
          }`}
        >
          {initials}
        </div>
        <div className="min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">
            {user?.full_name ?? `Usuario #${assignment.user_id}`}
          </p>
          <div className="flex items-center gap-2 flex-wrap">
            {assignment.location && (
              <span className="text-xs text-gray-400 truncate">
                {assignment.location}
              </span>
            )}
            <ResponseCountBadge count={assignment.response_count ?? 0} />
          </div>
        </div>
      </div>
      <div className="flex items-center gap-1.5 flex-shrink-0">
        <StatusBadge status={assignment.status} />
        <button
          onClick={() => onToggleStatus(assignment.id, assignment.status)}
          className={`p-1 rounded opacity-0 group-hover:opacity-100 transition-all ${
            isActive
              ? "text-gray-300 hover:text-orange-500 hover:bg-orange-50"
              : "text-gray-300 hover:text-green-600 hover:bg-green-50"
          }`}
          title={isActive ? "Desactivar asignacion" : "Reactivar asignacion"}
        >
          {isActive ? (
            <ToggleLeft className="h-4 w-4" />
          ) : (
            <ToggleRight className="h-4 w-4" />
          )}
        </button>
        <button
          onClick={() => onDelete(assignment.id)}
          className="p-1 rounded text-gray-300 hover:text-red-500 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition-all"
          title="Eliminar asignacion"
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
  onToggleStatus,
}: {
  group: SurveyGroup;
  onDelete: (id: number) => void;
  onAddUser: (surveyId: number, surveyTitle: string) => void;
  onToggleStatus: (id: number, current: AssignmentStatus) => void;
}) {
  const [open, setOpen] = useState(true);
  const all = [...group.encargados, ...group.brigadistas];
  const active = all.filter((a) => a.status === "active").length;
  const totalResponses = all.reduce((s, a) => s + (a.response_count ?? 0), 0);

  return (
    <div className="bg-gray-50 rounded-xl border border-gray-200 overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4 bg-white border-b border-gray-200">
        <button
          className="flex items-center gap-3 min-w-0 flex-1 text-left"
          onClick={() => setOpen((v) => !v)}
        >
          <div className="w-9 h-9 rounded-lg bg-primary-100 text-primary-700 flex items-center justify-center flex-shrink-0">
            <ClipboardList className="h-[18px] w-[18px]" />
          </div>
          <div className="min-w-0">
            <h3 className="font-semibold text-gray-900 truncate">
              {group.surveyTitle}
            </h3>
            <p className="text-xs text-gray-500 flex items-center gap-2 flex-wrap">
              <span>
                {all.length} asignado{all.length !== 1 ? "s" : ""}
              </span>
              {active > 0 && (
                <span className="text-green-600">
                  {active} activo{active !== 1 ? "s" : ""}
                </span>
              )}
              {totalResponses > 0 && (
                <span className="text-indigo-500">
                  {totalResponses}{" "}
                  {totalResponses === 1 ? "respuesta" : "respuestas"} totales
                </span>
              )}
            </p>
          </div>
          <ChevronDown
            className={`h-4 w-4 text-gray-400 ml-2 flex-shrink-0 transition-transform duration-200 ${
              open ? "rotate-180" : ""
            }`}
          />
        </button>
        <button
          onClick={() => onAddUser(group.surveyId, group.surveyTitle)}
          className="flex items-center gap-1.5 text-sm text-primary-600 hover:text-primary-700 font-medium px-3 py-1.5 rounded-lg hover:bg-primary-50 transition-colors ml-3 flex-shrink-0"
        >
          <Plus className="h-4 w-4" />
          Asignar usuario
        </button>
      </div>
      {open && (
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
                  <AssignedUserCard
                    key={a.id}
                    assignment={a}
                    onDelete={onDelete}
                    onToggleStatus={onToggleStatus}
                  />
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
                  <AssignedUserCard
                    key={a.id}
                    assignment={a}
                    onDelete={onDelete}
                    onToggleStatus={onToggleStatus}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      )}
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

  const totalResponses = assignments.reduce(
    (s, a) => s + (a.response_count ?? 0),
    0,
  );

  const stats = [
    {
      label: "Encuestas con asignados",
      value: groups.length,
      color: "text-gray-900",
    },
    {
      label: "Personas asignadas",
      value: assignments.length,
      color: "text-gray-700",
    },
    {
      label: "Activos",
      value: assignments.filter((a) => a.status === "active").length,
      color: "text-green-600",
    },
    {
      label: "Respuestas enviadas",
      value: totalResponses,
      color: "text-indigo-600",
    },
  ];

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
    if (
      !confirm(
        "Eliminar esta asignacion? Las respuestas ya enviadas se conservan.",
      )
    )
      return;
    try {
      await assignmentService.deleteAssignment(id);
      setAssignments((prev) => prev.filter((a) => a.id !== id));
    } catch (err) {
      console.error("Error deleting assignment:", err);
    }
  };

  const handleToggleStatus = async (
    id: number,
    current: AssignmentStatus,
  ) => {
    const next = current === "active" ? "inactive" : "active";
    try {
      await assignmentService.updateAssignment(id, { status: next });
      setAssignments((prev) =>
        prev.map((a) => (a.id === id ? { ...a, status: next } : a)),
      );
    } catch (err) {
      console.error("Error toggling status:", err);
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
          Una asignacion <span className="font-medium">activa</span> permite al
          usuario llenar la encuesta{" "}
          <span className="font-medium">multiples veces</span> desde la app
          movil. Puedes desactivarla para revocar el acceso sin borrar las
          respuestas previas.
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {stats.map((s) => (
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
              onToggleStatus={handleToggleStatus}
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
""".lstrip()

page_path = pathlib.Path(
    "/Users/dou1013/Documents/GithubProyects/brigadaWebCMS/src/app/dashboard/assignments/page.tsx"
)
page_path.write_text(PAGE_CONTENT, encoding="utf-8")
print(f"Written: {page_path.stat().st_size} bytes, {len(PAGE_CONTENT.splitlines())} lines")
