import { ColorSwatch, Group } from '@mantine/core';
import { Button } from '@/components/ui/button';
import { useEffect, useRef, useState, useCallback } from 'react';
import axios from 'axios';
import { motion } from "framer-motion";
import { SWATCHES } from '@/constants';
import { FaEraser, FaPen, FaImage } from 'react-icons/fa';
import { Slider } from "@/components/ui/slider";

interface GeneratedResult {
    expression: string;
    answer: string;
    unit: string;
}

interface Response {
    expr: string;
    result: string;
    unit: string;
    assign: boolean;
}

interface ApiResponse {
    data: Response[];
}

declare global {
  interface Window {
    MathJax: unknown;
  }
}
  

export default function Home() {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [isDrawing, setIsDrawing] = useState(false);
    const [color, setColor] = useState(SWATCHES[1]);
    const [reset, setReset] = useState(false);
    const [dictOfVars, setDictOfVars] = useState<Record<string, string>>({});
    const [result, setResult] = useState<GeneratedResult>();
    const [latexPosition, setLatexPosition] = useState({ x: 10, y: 200 });
    const [latexExpression, setLatexExpression] = useState<Array<string>>([]);
    const [isErasing, setIsErasing] = useState(false);
    const [brushSize, setBrushSize] = useState(3);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [history, setHistory] = useState<string[]>([]);
    const [redoStack, setRedoStack] = useState<string[]>([]);


    useEffect(() => {
        const canvas = canvasRef.current;
        if (canvas) {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight - canvas.offsetTop;
            const ctx = canvas.getContext('2d', { willReadFrequently: true });
            if (ctx) {
                ctx.fillStyle = 'black';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.lineCap = 'round';
            }
        }

        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.9/MathJax.js?config=TeX-MML-AM_CHTML';
        script.async = true;
        document.head.appendChild(script);

        script.onload = () => {
            window.MathJax.Hub.Config({
                tex2jax: { inlineMath: [['$', '$'], ['\\(', '\\)']] }
            });
        };

        return () => {
            document.head.removeChild(script);
        };
    }, []);

    const undo = useCallback(() => {
        if (history.length === 0) return;
        const canvas = canvasRef.current;
        const ctx = canvas?.getContext('2d');
        if (!canvas || !ctx) return;
        const last = history[history.length - 1];
        setRedoStack(prev => [...prev, canvas.toDataURL()]);
        setHistory(prev => prev.slice(0, -1));
        const img = new Image();
        img.onload = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0);
        };
        img.src = last;
    }, [history]);

    const redo = useCallback(() => {
        if (redoStack.length === 0) return;
        const canvas = canvasRef.current;
        const ctx = canvas?.getContext('2d');
        if (!canvas || !ctx) return;
        const next = redoStack[redoStack.length - 1];
        setHistory(prev => [...prev, canvas.toDataURL()]);
        setRedoStack(prev => prev.slice(0, -1));
        const img = new Image();
        img.onload = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0);
        };
        img.src = next;
    }, [redoStack]);


    useEffect(() => {
        const handler = (e: KeyboardEvent) => {
            if (e.ctrlKey && e.key === 'z') {
                e.preventDefault();
                if (e.shiftKey) {
                    redo();
                } else {
                    undo();
                }
            }
        };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, [undo, redo]);
    const saveHistory = useCallback(() => {
        const canvas = canvasRef.current;
        if (canvas) {
            setHistory(prev => [...prev, canvas.toDataURL()]);
            setRedoStack([]);
        }
    }, []);
    useEffect(() => {
        const handler = (e: KeyboardEvent) => {
            if (e.ctrlKey && e.key.toLowerCase() === 'z' && !e.shiftKey) {
                e.preventDefault();
                undo();
            }   
            if ((e.ctrlKey && e.key.toLowerCase() === 'y') || (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'z')) {
                e.preventDefault();
                redo();
            }
        };
    
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, [undo, redo]);
    

    const renderLatexToCanvas = useCallback((expression: string, answer: string) => {
        const latex = `${expression} = ${answer}`;
        setLatexExpression((prev) => [...prev, latex]);
    }, []);

    useEffect(() => {
        if (result) {
            renderLatexToCanvas(result.expression, result.answer);
        }
    }, [result, renderLatexToCanvas]);

    const resetCanvas = useCallback(() => {
        const canvas = canvasRef.current;
        if (canvas) {
            const ctx = canvas.getContext('2d', { willReadFrequently: true });
            if (ctx) {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.fillStyle = 'black';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
            }
        }
    }, []);

    useEffect(() => {
        if (reset) {
            resetCanvas();
            setLatexExpression([]);
            setResult(undefined);
            setDictOfVars({});
            setReset(false);
        }
    }, [reset, resetCanvas]);

    const startDrawing = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        saveHistory();

        ctx.beginPath();
        ctx.moveTo(e.nativeEvent.offsetX, e.nativeEvent.offsetY);
        ctx.lineWidth = brushSize;
        ctx.strokeStyle = isErasing ? '#000000' : color;
        setIsDrawing(true);
    }, [brushSize, color, isErasing, saveHistory]);

    const draw = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
        if (!isDrawing) return;
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        ctx.lineWidth = brushSize;
        ctx.strokeStyle = isErasing ? '#000000' : color;
        ctx.lineTo(e.nativeEvent.offsetX, e.nativeEvent.offsetY);
        ctx.stroke();
    }, [isDrawing, brushSize, color, isErasing]);

    const stopDrawing = useCallback(() => {
        setIsDrawing(false);
    }, []);

    const toggleErase = useCallback(() => {
        setIsErasing(prev => !prev);
    }, []);

           const handleImageUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
                const file = e.target.files?.[0];
                if (!file) return;
                const reader = new FileReader();
                reader.onload = (event) => {
                    const img = new Image();
                    img.onload = () => {
                        const canvas = canvasRef.current;
                        if (!canvas) return;
                        const ctx = canvas.getContext('2d', { willReadFrequently: true });
                        if (!ctx) return;
                        const canvasWidth = canvas.width;
                        const canvasHeight = canvas.height;
                        // Clear canvas and set black background
                        ctx.clearRect(0, 0, canvasWidth, canvasHeight);
                        ctx.fillStyle = 'black';
                        ctx.fillRect(0, 0, canvasWidth, canvasHeight);
                        // Scale image to full canvas width
                        const targetWidth = canvasWidth;
                        const scale = targetWidth / img.width;
                        let drawHeight = img.height * scale;
                        // If height exceeds 95% of canvas height, shrink further
                        const maxAllowedHeight = canvasHeight * 0.90;
                        if (drawHeight > maxAllowedHeight) {
                            const heightScale = maxAllowedHeight / drawHeight;
                            drawHeight *= heightScale;
                        }
                        const drawWidth = drawHeight * (img.width / img.height); 
                        const offsetX = (canvasWidth - drawWidth) / 2; 
                        const offsetY = canvasHeight - drawHeight;     
                        ctx.drawImage(img, offsetX, offsetY, drawWidth, drawHeight);
                    };
                    img.src = event.target?.result as string;
                };
                reader.readAsDataURL(file);
            }, []);


    
                

    const runRoute = useCallback(async () => {
        const canvas = canvasRef.current;
        if (canvas) {
            try {
                const response = await axios.post<ApiResponse>(
                    `${import.meta.env.VITE_API_URL}/calculate/analyze/`,
                    {
                        image: canvas.toDataURL('image/png'),
                        dict_of_vars: dictOfVars
                    }
                );  
                response.data.data.forEach((item) => {
                    if (item.assign) {
                        setDictOfVars(prev => ({
                            ...prev,
                            [item.expr]: item.result
                        }));
                    }
                });  
                const ctx = canvas.getContext('2d', { willReadFrequently: true });
                const imageData = ctx!.getImageData(0, 0, canvas.width, canvas.height);
                let minX = canvas.width, minY = canvas.height, maxX = 0, maxY = 0;
    
                for (let y = 0; y < canvas.height; y++) {
                    for (let x = 0; x < canvas.width; x++) {
                        const i = (y * canvas.width + x) * 4;
                        if (imageData.data[i + 3] > 0) {
                            minX = Math.min(minX, x);
                            minY = Math.min(minY, y);
                            maxX = Math.max(maxX, x);
                            maxY = Math.max(maxY, y);
                        }
                    }
                }
    
                const centerX = (minX + maxX) / 2;
                const centerY = (minY + maxY) / 2;
    
                setLatexPosition({ x: centerX, y: centerY });
    
                response.data.data.forEach((data) => {
                    
                    setTimeout(() => {
                        setResult({
                            expression: data.expr,
                            answer: data.unit ? `${data.result} ${data.unit}` : `${data.result}`,
                            unit: data.unit
                        });
    
                        resetCanvas(); 
                    }, 500); 
                });
            } catch (error) {
                console.error('API Error:', error);
            }
        }
    }, [dictOfVars, resetCanvas]);
    
    return (
        <>
            <div className='fixed top-4 left-0 right-0 flex justify-center items-center gap-4 z-20'>
                <Button onClick={() => setReset(true)} className='bg-black text-white hover:bg-gray-800'>Reset</Button>
                <Button onClick={() => fileInputRef.current?.click()} className='bg-black text-white hover:bg-gray-800'>
                    <FaImage className="w-4 h-4" />
                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleImageUpload}
                        accept="image/*"
                        className="hidden"
                    />
                </Button>
                <Button
                    onClick={toggleErase}
                    className={`bg-black text-white hover:bg-gray-800 ${isErasing ? 'bg-gray-700' : ''}`}
                >
                    {isErasing ? <FaPen className="w-4 h-4" /> : <FaEraser className="w-4 h-4" />}
                </Button>
                <div className="flex items-center gap-2 w-32">
                    <Slider
                        value={[brushSize]}
                        max={20}
                        min={1}
                        step={1}
                        onValueChange={(value) => setBrushSize(value[0])}
                        className="w-full"
                    />
                    <span className="text-white text-sm w-8">{brushSize}px</span>
                </div>
                <Group gap="xs">
                    {SWATCHES.map((swatch) => {
                        const isSelected = color === swatch && !isErasing;
                        const isWhite = swatch.toLowerCase() === "#ffffff" || swatch.toLowerCase() === "rgb(255, 255, 255)";
                        return (
                            <ColorSwatch
                                key={swatch}
                                color={swatch}
                                onClick={() => {
                                    setColor(swatch);
                                    setIsErasing(false);
                                }}
                                className="cursor-pointer hover:opacity-90 transition-opacity"
                                size={24}
                            >
                                {isSelected && (
                                    <FaPen className={`w-2 h-2 ${isWhite ? "text-black" : "text-white"}`} />
                                )}
                            </ColorSwatch>
                        );
                    })}
                </Group>
                <Button onClick={runRoute} className='bg-blue-600 text-white hover:bg-blue-700'>Calculate</Button>
            </div>

            <canvas
                ref={canvasRef}
                id='canvas'
                className='absolute top-0 left-0 w-full h-full'
                onMouseDown={startDrawing}
                onMouseMove={draw}
                onMouseUp={stopDrawing}
                onMouseOut={stopDrawing}
            />

            {latexExpression && latexExpression.map((latex, index) => (
                <motion.div
                    key={index}
                    drag
                    dragMomentum={false}
                    style={{ position: "absolute", top: latexPosition.y, left: latexPosition.x }}
                    className="p-2 text-white rounded shadow-md bg-black bg-opacity-80"
                >
                    <div className="latex-content">{latex}</div>
                </motion.div>
            ))}
        </>
    );
}
