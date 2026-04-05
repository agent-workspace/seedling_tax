import React from 'react';
import TopBar from './TopBar';
import MenuBar from './MenuBar';
import Sidebar from './Sidebar';
import StatusBar from './StatusBar';

export default function Layout({
  activeModule,
  onModuleChange,
  sidebarItems,
  activeSidebarItem,
  onSidebarChange,
  statusHints,
  children,
}) {
  return (
    <div className="app-layout">
      <TopBar />
      <MenuBar activeModule={activeModule} onModuleChange={onModuleChange} />
      <div className="app-body">
        <Sidebar items={sidebarItems} activeItem={activeSidebarItem} onItemChange={onSidebarChange} />
        <div className="main-content">{children}</div>
      </div>
      <StatusBar hints={statusHints} />
    </div>
  );
}
