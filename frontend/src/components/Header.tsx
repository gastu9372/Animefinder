import React from "react";
import { IconLogo } from "./Icons";

export const Header: React.FC = () => {
  return (
    <header className="site-header">
      <div className="site-header-inner">
        <a href="/" className="logo-brand">
          <IconLogo size={28} />
          <span className="logo-title">
            Anime<span className="logo-accent">Finder</span>
          </span>
        </a>
      </div>
    </header>
  );
};
