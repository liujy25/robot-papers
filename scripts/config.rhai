let titles_type = ["Dataset", "Survey", "Review", "Overview"];
let titles_model = [];
let titles_method = [
    "Certifiable", "Self-Supervised", "Semi-Supervised", "Unsupervised", "Fusion", "Navigation", 
    "Detect", "Decision", "Calibration", "Reinforcement", "Relocalization", "loop", "global", "outlier", 
    "localization", "dynamic", "graph", "clique", "HD map", "reconstruction", "robot", 
    "Guassian", "road", "robust", "simulation", "simulator", "dataset", "Deformable", "closed-form", 
    "geometric", "benchmark", "evaluation", "prediction", "multi-view", "grasp", "field", "point cloud", "lidar", 
    "trajectory", "trajectories", "cluster", "GPT", "LLM", "embodied", "pose"

    "VLA", "VLN", "VLM", "LLM", "Foundation Model", "Generalist", "Open-vocabulary", 
    "Large Language Model", "Vision-Language", "Multimodal", "Transformer", 
    "GPT", "CLIP", "Chain-of-Thought", "Prompt", "In-context", "sim", "sim-to-real",

    "Diffusion", "Score-based", "Generative", "Diffusion Policy", "flow matching", "flow",

    "Reinforcement Learning", "RL", "Imitation Learning", "Behavior Cloning", 
    "Inverse RL", "Offline RL", "Meta-learning", "Self-supervised", 
    "Semi-supervised", "Unsupervised", "Zero-shot", "Few-shot", "One-shot",
    "End-to-End", "Sim-to-Real", "Domain Randomization", "Curriculum",

    "NeRF", "Gaussian", "3DGS", "Implicit", "Affordance", "Scene Graph", 
    "Topological", "Semantic Map", "Occupancy", "Point Cloud", "RGB-D", "Tactile",

    "MPC", "Model Predictive Control", "Dynamics", "Kinematics", 
    "Compliance", "Impedance", "Admittance", "Torque", "Force", 
    "World Model", "Predictive"
];
let titles_task = [
    "SLAM", "Odometry", "Registration", "Exploration", "Long-term", "mapping", "Multi-session", 
    "Planning", "Optimization", "Estimation", "Control", "Detection", "Segmentation", "Life", "estimator",

    "Embodied", "Manipulation", "Grasping", "Navigation", "Mobile Manipulation", 
    "Locomotion", "Rearrangement", "Assembly", "Insertion", "Picking", "Placing",

    "Dexterous", "In-hand", "Bimanual", "Multi-finger", "Contact-rich", 
    "Fine-grained", "Interactive", "Teleoperation", "Human-Robot", "HRI",
    
    "VLN", "Instruction Following", "Visual Navigation", "ObjectNav", 
    "PointNav", "Exploration", "Social Navigation",
    
    "Task Planning", "Motion Planning", "TAMP", "Long-horizon", "Path Planning", "localmotion",
];
let titles =  titles_model + titles_method + titles_type;
let authors_array = ["Shaojie Shen", "Luca Carlone", "Yoshua Bengio", "Frank Dellaert", "Wolfram Burgard", "Davide Scaramuzza", "Marc Pollefeys", "Andrew Davison", "Daniel Cremers", "Heng Yang", "Fei Gao", 
"Tong Qin", "Wenchao Ding", "Fu Zhang", "Hesheng Wang", "Huan Yin", "Peng Yin", "Yue Wang", "Hang Zhao", "Xieyuanli Chen", "Boyu Zhou", "Timothy D. Barfoot", "Marc Pollefeys", "Kasra Khosoussi",
"Fang Bai", "kaiming he", "Kevin Doherty", "shoudong huang", "Guoquan Huang", "Yue Pan", "Timothy D. Barfoot", "Jonathan P. How", "Guofeng Zhang", "Cyrill Stachniss", "Javier Civera", "Yulun Tian", "Jose Luis Blanco Claraco",
"sida peng", "cewu Lu", "feifei li", "li feifei"];

let conferences = [
    // AI
    "AAAI", "CORL", "RA-L", "RAL", "TMECH", "TASE", "IJRR", "ICRA", "IROS", "RSS", "TRO",
    // CV
    "CVPR", "ECCV", "ICCV", "SIGGRAPH",
    // Robotics
    "Transactions on Robotics", "International Journal of Robotics Research", "Robotics and Automation Letters"
    // ML
    "ICLR", "ICML", "NeurIPS", "NIPS",
];

let start = conferences.shift();
let conferences_rg = conferences.reduce(|sum, v| sum + "|" + v, start);
let conferences_rg = "(" + conferences_rg + ")([\\s'-]*\\d+)?";

let start = titles.shift();
let title_rg = titles.reduce(|sum, v| sum + "|" + v, start);

let start = authors_array.shift();
let authors_rg = authors_array.reduce(|sum, v| sum + "|" + v, start);

export title_rg;
export authors_rg;
export conferences_rg;
