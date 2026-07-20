import React, { useEffect, useState } from "react";
import NavBar from "./NavBar";
import Login from "../pages/Login";
import Notes from "./Notes";

function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    fetch("/me", {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`
      }
    }).then((r) => {
      if (r.ok) {
        r.json().then((user) => setUser(user));
      }
    });
  }, []);

  const onLogin = (token, user) => {
    localStorage.setItem("token", token);
    setUser(user);
  };

  if (!user) return <Login onLogin={onLogin} />;

  return (
    <>
      <NavBar setUser={setUser} />
      <main>
        <Notes user={user} />
      </main>
    </>
  );
}

export default App;
