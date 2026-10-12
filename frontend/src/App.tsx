import { useEffect, useState } from "react";
import ApplicationView from "./ApplicationView";
import Dashboard from "./Dashboard";
import ProfileEditor from "./ProfileEditor";

type Route = { name: "home" } | { name: "profile" } | { name: "app"; id: number };

function parse(hash: string): Route {
  const m = /^#\/app\/(\d+)$/.exec(hash);
  if (m) return { name: "app", id: Number(m[1]) };
  return hash === "#/profile" ? { name: "profile" } : { name: "home" };
}

export default function App() {
  const [route, setRoute] = useState<Route>(parse(window.location.hash));
  useEffect(() => {
    const h = () => setRoute(parse(window.location.hash));
    window.addEventListener("hashchange", h);
    return () => window.removeEventListener("hashchange", h);
  }, []);
  const go = (hash: string) => { window.location.hash = hash; };

  return (
    <>
      <a className="skip" href="#main">Pular para o conteúdo</a>
      <div id="main">
        {route.name === "home" && <Dashboard onOpen={(id) => go(`#/app/${id}`)} onProfile={() => go("#/profile")} />}
        {route.name === "profile" && <ProfileEditor onBack={() => go("#/")} />}
        {route.name === "app" && <ApplicationView key={route.id} id={route.id} onBack={() => go("#/")} />}
      </div>
    </>
  );
}
