/**
 * Simple frontend logger to help with debugging
 */
export class Logger {
    private static instance: Logger;
    private readonly loggingEnabled: boolean = true;

    private constructor() {
        // Private constructor to enforce singleton pattern
    }

    public static getInstance(): Logger {
        if (!Logger.instance) {
            Logger.instance = new Logger();
        }
        return Logger.instance;
    }

    public log(message: string, data?: any): void {
        if (this.loggingEnabled) {
            console.log(`[INFO] ${message}`, data || '');
        }
    }

    public error(message: string, error?: any): void {
        if (this.loggingEnabled) {
            console.error(`[ERROR] ${message}`, error || '');
            
            // If error is an Error object, log stack trace as well
            if (error instanceof Error) {
                console.error(`[STACK] ${error.stack}`);
            }
        }
    }

    public warn(message: string, data?: any): void {
        if (this.loggingEnabled) {
            console.warn(`[WARN] ${message}`, data || '');
        }
    }

    public debug(message: string, data?: any): void {
        if (this.loggingEnabled) {
            console.debug(`[DEBUG] ${message}`, data || '');
        }
    }
}

// Export a default instance for convenience
export default Logger.getInstance();