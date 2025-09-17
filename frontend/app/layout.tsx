import React from 'react';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    return (
        <html>
            <body>
                <div>
                    <header>
                        <h1>My App</h1>
                    </header>
                    <main>
                        {children}
                    </main>
                    <footer>
                        <p>&copy; 2023 My App</p>
                    </footer>
                </div>
            </body>
        </html>
    );
};

export default Layout;