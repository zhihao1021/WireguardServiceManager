import { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import HomePage from "@/views/homePage";
import LoginPage from "@/views/loginPage";

export default function App(): ReactNode {
    return <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/" />} />
    </Routes>
}