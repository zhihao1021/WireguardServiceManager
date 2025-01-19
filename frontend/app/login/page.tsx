"use client"
import { ChangeEvent, KeyboardEvent, ReactNode, Suspense, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";

import req from "@/config/axios";
import JWT from "@/schemas/jwt";

import style from "./page.module.scss";

function Conetent(): ReactNode {
    const [loading, setLoading] = useState<boolean>(false);
    const [code, setCode] = useState<string | null>();
    const [joinKey, setJoinKey] = useState<string>("");
    const searchParams = useSearchParams();
    const newCode = searchParams.get("code");
    const router = useRouter();

    const onJoinKeyChage = useCallback((event: ChangeEvent<HTMLInputElement>) => {
        setJoinKey(event.target.value);
    }, []);

    const onKeyDown = useCallback((event: KeyboardEvent<HTMLInputElement>) => {
        if (event.key !== "Enter" || code === null) return;

        setLoading(true);
        req.post(
            "/oauth", { code: code, join_key: joinKey }
        ).then(response => {
            const data = response.data as JWT;
            localStorage.setItem("token_type", data.token_type);
            localStorage.setItem("access_token", data.access_token);
            router.push("/");
        }).catch(() => {
            setCode(null);
            setJoinKey("");
            setLoading(false);
        })
    }, [code, joinKey, router]);

    useEffect(() => {
        setCode(current => {
            return current ?? newCode
        });
        if (newCode) router.replace(location.pathname);
    }, [newCode, router]);

    return <div className={style.loginPage}>
        <div className={style.box}>
            <h1>Login</h1>
            <div className={style.content} data-loading={loading || code === undefined}>
                <div className={style.loading} />
                {
                    code == null ? <Link href={process.env.NEXT_PUBLIC_OAUTH_URL ?? ""}>
                        <img src="/discord-logo-white.svg" />
                    </Link> : <div className={style.joinKey}>
                        <div className={style.inputBox}>
                            <span className="ms">key</span>
                            <input
                                value={joinKey}
                                onChange={onJoinKeyChage}
                                onKeyDown={onKeyDown}
                                placeholder="Join Key"
                            />
                        </div>
                        <div className={style.info}>If you have logged in before, please press Enter directly.</div>
                    </div>
                }
            </div>
        </div>
    </div>
}
export default function LoginPage(): ReactNode {
    return <Suspense>
        <Conetent />
    </Suspense>
}