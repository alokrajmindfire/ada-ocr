import NotFound from '@/components/layout/NotFound';
import React, { lazy, memo } from 'react';
import { Routes, Route } from 'react-router-dom';

const HomePage = lazy(() => import('@/pages/Home'));
const DocumentPage = lazy(() => import('@/pages/DocumentPage'));

export const AppRoutes: React.FC = memo(() => {
  return (
     <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/documents/:id" element={<DocumentPage />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
  );
});

AppRoutes.displayName = 'AppRoutes';
