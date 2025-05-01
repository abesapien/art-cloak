/**
 * Simple frontend logger to help with debugging
 */
export class Logger {
    constructor() {
        this.loggingEnabled = true;
    }

    static getInstance() {
        if (!Logger.instance) {
            Logger.instance = new Logger();
        }
        return Logger.instance;
    }

    log(message, data) {
        if (this.loggingEnabled) {
            console.log(`[INFO] ${message}`, data || '');
        }
    }

    error(message, error) {
        if (this.loggingEnabled) {
            console.error(`[ERROR] ${message}`, error || '');
            
            // If error is an Error object, log stack trace as well
            if (error instanceof Error) {
                console.error(`[STACK] ${error.stack}`);
            }
        }
    }

    warn(message, data) {
        if (this.loggingEnabled) {
            console.warn(`[WARN] ${message}`, data || '');
        }
    }

    debug(message, data) {
        if (this.loggingEnabled) {
            console.debug(`[DEBUG] ${message}`, data || '');
        }
    }
}

// Export a default instance for convenience
export default Logger.getInstance();