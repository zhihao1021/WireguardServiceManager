export function timeParser(time: number): string {
    if (!time) return "從未";
    const delta = Date.now() - (time * 1000);

    const seconds = Math.round(delta / 1000);
    if (seconds < 60) return `${seconds} 秒前`;
    const minutes = Math.round(seconds / 60);
    if (minutes < 60) return `${minutes} 分 ${seconds % 60} 秒前`;
    const hours = Math.round(minutes / 60);
    if (hours < 24) return `${hours} 小時前`;
    return `${Math.round(hours / 24)} 天前`;
}