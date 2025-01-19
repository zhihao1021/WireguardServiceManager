"use client"
import { jwtDecode } from "jwt-decode";
import { redirect, useRouter } from "next/navigation";
import { ReactNode, useCallback, useEffect, useMemo, useState } from "react";

import req from "@/config/axios";
import JWT from "@/schemas/jwt";
import UserData from "@/schemas/userData";
import UserWithConnection from "@/schemas/userWithConnection";

import style from "./page.module.scss";
import Link from "next/link";
import CopyBox from "./components/copyBox";
import { timeParser } from "./utils/timeParser";

async function getUserData(): Promise<UserData> {
    const token = localStorage.getItem("access_token");
    let data: UserData = jwtDecode(token as string);
    if (data.exp * 1000 < Date.now()) {
        throw Error("Token expired");
    }

    if (data.exp * 1000 - Date.now() < 72 * 3600 * 1000) {
        const response = await req.put("/oauth");
        const jwt: JWT = response.data;
        localStorage.setItem("token_type", jwt.token_type);
        localStorage.setItem("access_token", jwt.access_token);
        data = jwtDecode(jwt.access_token);
    }

    return data;
}

async function getUsers(): Promise<Array<UserWithConnection>> {
    const response = await req.get("/connection");
    return response.data;
}

async function getConnectionString(): Promise<string> {
    const response = await req.get("/connection/connect");
    return btoa(response.data);
}

export default function App(): ReactNode {
    const [userData, setUserData] = useState<UserData>();
    const [connectionString, setConnectionString] = useState<string>("");
    const [userList, setUserList] = useState<Array<UserWithConnection>>([]);
    const [status, setStatus] = useState<{ [publicKey: string]: number }>({});
    const [_, setWs] = useState<WebSocket>();
    const router = useRouter();

    const userConnectionInfo: UserWithConnection | undefined = useMemo(() => {
        return userList.find(v => v.discord_id == userData?.discord_id);
    }, [userData, userList]);

    const connectWs = useCallback(() => {
        let endPoint = process.env.NEXT_PUBLIC_API_END_POINT;
        if (endPoint === undefined)
            return;

        if (!endPoint.startsWith("http"))
            endPoint = `${location.origin}${endPoint}`;

        const ws = new WebSocket(`${endPoint.replace("http", "ws")}/connection`);
        ws.onopen = () => ws.send(localStorage.getItem("access_token") ?? "")
        ws.onmessage = message => {
            const rawData: Blob = message.data;
            rawData.text().then(dataString => setStatus(JSON.parse(dataString)));
        }
        ws.onclose = () => setTimeout(connectWs, 1000);
        setWs(ws);
    }, []);

    const logout = useCallback(() => {
        localStorage.removeItem("token_type");
        localStorage.removeItem("access_token");
        router.push("/login");
    }, [router]);

    useEffect(() => {
        getUserData().then(userData => {
            setUserData(userData)
            getUsers().then(response => setUserList(response));
            getConnectionString().then(response => setConnectionString(response));
            connectWs();
        }).catch(() => {
            redirect("/login");
        })
    }, [connectWs]);

    if (userData === undefined)
        return undefined;

    return <div className={style.app}>
        <div className={style.userInfo}>
            <img src={userData.display_avatar} />
            <div className={style.displayName}>{userData.display_name}</div>
            <div className={style.ipAddress}>
                {
                    userConnectionInfo ? <CopyBox
                        text={userConnectionInfo.connection.ip_address}
                    /> : undefined
                }
            </div>
            <Link
                href={`data:text/plain;base64,${connectionString}`}
                download="connection.conf"
                target="_blank"
                className={style.conf}
            >
                <span className="ms">download</span>
                <span>Conf.</span>
            </Link>
            <button className={style.logout} onClick={logout}>
                <span className="ms">logout</span>
                <span>Logout</span>
            </button>
        </div>
        <div className={style.clients}>
            {
                userList.map(data => <div
                    key={data.connection.public_key}
                    className={style.statusBox}
                >
                    <div className={style.user}>
                        <img src={data.display_avatar} />
                        <div>{data.display_name}</div>
                    </div>
                    <hr />
                    <div className={style.userIp}>
                        <div className={style.key}>IP</div>
                        <CopyBox text={data.connection.ip_address} />
                    </div>
                    <div className={style.publicKey}>
                        <div className={style.key}>Public Key</div>
                        <div
                            className={style.value}
                            title={data.connection.public_key}
                        >{data.connection.public_key}</div>
                    </div>
                    <div className={style.lastHandshakes}>
                        <div className={style.key}>Last Seen</div>
                        <div
                            className={style.value}
                        >{timeParser(status[data.connection.public_key])}</div>
                    </div>
                </div>)
            }
        </div>
    </div>
}