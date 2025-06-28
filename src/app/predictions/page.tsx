export default function PredictionsPage() {
    return (
        <>
            <header className="border-b bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60">         
                <div className="container mx-auto px-4 py-4">           
                    <div className="flex items-center justify-between">             
                        <div className="flex items-center space-x-4">               
                            <h1 className="text-2xl font-bold text-primary">Griffith Punters Club</h1>               
                            {/* <Badge variant="secondary">Beta</Badge>              */}
                        </div>             
                        <div className="flex items-center space-x-4">               
                            <div className="flex items-center space-x-2 bg-green-50 px-3 py-1 rounded-full">                 
                                {/* <Coins className="h-4 w-4 text-green-600" />                  */}
                                <span className="font-medium text-green-700">1,250 GP</span>               
                            </div>               
                            {/* <Avatar>                 
                                <AvatarImage src="/placeholder.svg?height=32&width=32" />                 
                                <AvatarFallback>JD</AvatarFallback>               
                            </Avatar>              */}
                        </div>           
                    </div>         
                </div>       
            </header>
            <p>test</p>
        </>
    );
}