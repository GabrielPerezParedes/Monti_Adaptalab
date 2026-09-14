import { FormEvent, useCallback, useEffect, useState } from "react";
import { api, patch, post } from "./api";

type UserRow = {
  id: string;
  login: string;
  display_name: string;
  role: string;
  is_active: boolean;
};
type Grade = { id: string; name: string; sort_order: number; is_active: boolean };
type Subject = { id: string; name: string; is_active: boolean };
type Assignment = { id: string; teacher_user_id: string; subject_id: string };
type Enrollment = {
  id: string;
  student_user_id: string;
  grade_id: string;
  subject_id: string;
  is_active: boolean;
};

export default function Admin() {
  const [users, setUsers] = useState<UserRow[]>([]);
  const [grades, setGrades] = useState<Grade[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const [userForm, setUserForm] = useState({
    login: "",
    display_name: "",
    role: "student",
    password: "",
  });
  const [gradeName, setGradeName] = useState("");
  const [subjectName, setSubjectName] = useState("");
  const [assignForm, setAssignForm] = useState({ teacher_user_id: "", subject_id: "" });
  const [enrollForm, setEnrollForm] = useState({
    student_user_id: "",
    grade_id: "",
    subject_id: "",
  });

  const refresh = useCallback(async () => {
    try {
      const [u, g, s, a, e] = await Promise.all([
        api<UserRow[]>("/admin/users"),
        api<Grade[]>("/admin/grades"),
        api<Subject[]>("/admin/subjects"),
        api<Assignment[]>("/admin/teacher-assignments"),
        api<Enrollment[]>("/admin/enrollments"),
      ]);
      setUsers(u);
      setGrades(g);
      setSubjects(s);
      setAssignments(a);
      setEnrollments(e);
      setError("");
    } catch (err) {
      setError((err as Error).message);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function createUser(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await api("/admin/users", post(userForm));
      setUserForm({ login: "", display_name: "", role: "student", password: "" });
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function toggleUser(user: UserRow) {
    setBusy(true);
    try {
      await api(`/admin/users/${user.id}`, patch({ is_active: !user.is_active }));
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="shell">
      <section className="panel">
        <div className="activity-heading">
          <h1>Administración escolar</h1>
        </div>
        <p className="field-hint">
          Gestiona usuarios, grados, asignaturas, asignaciones docentes y
          matrículas.
        </p>
        {error ? (
          <p className="notice error" role="alert">
            {error}
          </p>
        ) : null}
      </section>

      <section className="panel">
        <h2>Usuarios</h2>
        <form className="stack" onSubmit={createUser}>
          <label>
            Login
            <input
              value={userForm.login}
              onChange={(e) => setUserForm({ ...userForm, login: e.target.value })}
              required
            />
          </label>
          <label>
            Nombre visible
            <input
              value={userForm.display_name}
              onChange={(e) =>
                setUserForm({ ...userForm, display_name: e.target.value })
              }
              required
            />
          </label>
          <label>
            Rol
            <select
              value={userForm.role}
              onChange={(e) => setUserForm({ ...userForm, role: e.target.value })}
            >
              <option value="student">Alumno</option>
              <option value="teacher">Profesor</option>
              <option value="admin">Administrador</option>
            </select>
          </label>
          <label>
            Contraseña (≥10)
            <input
              type="password"
              value={userForm.password}
              onChange={(e) =>
                setUserForm({ ...userForm, password: e.target.value })
              }
              minLength={10}
              required
            />
          </label>
          <button disabled={busy}>Crear usuario</button>
        </form>
        <ul className="plain-list">
          {users.map((u) => (
            <li key={u.id}>
              <strong>{u.display_name}</strong> · {u.login} · {u.role} ·{" "}
              {u.is_active ? "activo" : "inactivo"}{" "}
              <button className="secondary" type="button" onClick={() => toggleUser(u)}>
                {u.is_active ? "Desactivar" : "Activar"}
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="panel">
        <h2>Grados</h2>
        <form
          className="stack"
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            try {
              await api("/admin/grades", post({ name: gradeName, sort_order: grades.length + 1 }));
              setGradeName("");
              await refresh();
            } catch (err) {
              setError((err as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <label>
            Nombre
            <input value={gradeName} onChange={(e) => setGradeName(e.target.value)} required />
          </label>
          <button disabled={busy}>Crear grado</button>
        </form>
        <ul className="plain-list">
          {grades.map((g) => (
            <li key={g.id}>
              {g.name} (orden {g.sort_order})
            </li>
          ))}
        </ul>
      </section>

      <section className="panel">
        <h2>Asignaturas</h2>
        <form
          className="stack"
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            try {
              await api("/admin/subjects", post({ name: subjectName }));
              setSubjectName("");
              await refresh();
            } catch (err) {
              setError((err as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <label>
            Nombre
            <input
              value={subjectName}
              onChange={(e) => setSubjectName(e.target.value)}
              required
            />
          </label>
          <button disabled={busy}>Crear asignatura</button>
        </form>
        <ul className="plain-list">
          {subjects.map((s) => (
            <li key={s.id}>{s.name}</li>
          ))}
        </ul>
      </section>

      <section className="panel">
        <h2>Asignación profesor → asignatura</h2>
        <form
          className="stack"
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            try {
              await api("/admin/teacher-assignments", post(assignForm));
              await refresh();
            } catch (err) {
              setError((err as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <label>
            Profesor
            <select
              value={assignForm.teacher_user_id}
              onChange={(e) =>
                setAssignForm({ ...assignForm, teacher_user_id: e.target.value })
              }
              required
            >
              <option value="">Selecciona</option>
              {users
                .filter((u) => u.role === "teacher")
                .map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.display_name}
                  </option>
                ))}
            </select>
          </label>
          <label>
            Asignatura
            <select
              value={assignForm.subject_id}
              onChange={(e) =>
                setAssignForm({ ...assignForm, subject_id: e.target.value })
              }
              required
            >
              <option value="">Selecciona</option>
              {subjects.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </label>
          <button disabled={busy}>Asignar</button>
        </form>
        <ul className="plain-list">
          {assignments.map((a) => (
            <li key={a.id}>
              {a.teacher_user_id} → {a.subject_id}
            </li>
          ))}
        </ul>
      </section>

      <section className="panel">
        <h2>Matrículas</h2>
        <form
          className="stack"
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            try {
              await api("/admin/enrollments", post(enrollForm));
              await refresh();
            } catch (err) {
              setError((err as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <label>
            Alumno
            <select
              value={enrollForm.student_user_id}
              onChange={(e) =>
                setEnrollForm({ ...enrollForm, student_user_id: e.target.value })
              }
              required
            >
              <option value="">Selecciona</option>
              {users
                .filter((u) => u.role === "student")
                .map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.display_name}
                  </option>
                ))}
            </select>
          </label>
          <label>
            Grado
            <select
              value={enrollForm.grade_id}
              onChange={(e) => setEnrollForm({ ...enrollForm, grade_id: e.target.value })}
              required
            >
              <option value="">Selecciona</option>
              {grades.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Asignatura
            <select
              value={enrollForm.subject_id}
              onChange={(e) =>
                setEnrollForm({ ...enrollForm, subject_id: e.target.value })
              }
              required
            >
              <option value="">Selecciona</option>
              {subjects.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </label>
          <button disabled={busy}>Matricular</button>
        </form>
        <ul className="plain-list">
          {enrollments.map((e) => (
            <li key={e.id}>
              {e.student_user_id} · {e.grade_id} · {e.subject_id} ·{" "}
              {e.is_active ? "activa" : "inactiva"}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
