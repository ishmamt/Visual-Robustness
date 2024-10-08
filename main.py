from generator import Generator
from models.llava import LLaVa
from dataset import VQADataset
from utils import Logger
from report import VQAReporter
from tqdm import tqdm
import os
# ------------------------------------------------------------------------------------------------------

CREATE_DATASETS = False
RUN_EXPERIMENTS = True

# Important Data for windows
# name = "val"
# questionsJSON = r"..\Hierarchical Co-Attention\Data\VQA\val\questions\val_quest_3K.json"
# annotationsJSON = r"..\Hierarchical Co-Attention\Data\VQA\val\annotations\val_ann_3K.json"
# imageDirectory = r"..\Hierarchical Co-Attention\Data\VQA\val\images\val3K"
# imagePrefix = None
# outputPath = r"."
# logPath = r"."
# reportPath = r"."

# Important Data for Linux (Colab)
name = "val"
annotationsJSON = "/kaggle/input/vqa-dataset/v2_mscoco_val2014_annotations.json"
questionsJSON = "/kaggle/input/vqa-dataset/v2_OpenEnded_mscoco_val2014_questions.json"
# imageDirectory = "Data/val3K"
imageDirectory = "/kaggle/input/vqa-dataset/OutputImages/OutputImages/"
imagePrefix = None
outputPath = "/kaggle/input/vqa-dataset/OutputImages/"
#outputPath = "Data/test_save/"
logPath = "/kaggle/output/"
reportPath = "/kaggle/output/"


# Creating a logger
logger = Logger(logPath)
logger.info("Starting experiment.")


# Transformation of dataset
dataset = VQADataset(name, questionsJSON, annotationsJSON, imageDirectory, imagePrefix, logger)
logger.info("VQA2.0 dataset loaded.")

if CREATE_DATASETS:
    generator = Generator(dataset, logger)
    # transformationsList = ["Defocus-blur_L1"]
    transformationsList = list(generator.validTransformations.keys())[23:]
    generator.transform(transformationsList, outputPath=outputPath)


if RUN_EXPERIMENTS:
    # Loading a model
    model = LLaVa(logger)

    for imageDir in os.listdir(imageDirectory):
        # Transformation of dataset
        imageDirectoryMultiple = os.path.join(imageDirectory, imageDir)
        dataset = VQADataset(name, questionsJSON, annotationsJSON, imageDirectoryMultiple, imagePrefix, logger)
        logger.info(f"VQA2.0 dataset loaded for {imageDirectoryMultiple}.")
        
        # Creating report
        reportPathMultiple = os.path.join(reportPath, imageDir)
        reporter = VQAReporter(model.name, imageDirectoryMultiple, reportPathMultiple, logger)

        # Computing accuracy
        totalAnswered = 0
        correctlyAnswered = 0
        verbose = 100
        saveAfter = 50

        pBar = tqdm(total=len(dataset))  # progress bar

        for idx in range(len(dataset)):
            pBar.update(1)
            image, questions, answers, imageId, questionIds, questionTypes = dataset[idx]

            for idx, question in enumerate(questions):
                try:
                    prediction = model.predict(image, question)
                    if answers[idx] == prediction:
                        correct = True
                        correctlyAnswered += 1
                    else:
                        correct = False
                        
                    totalAnswered += 1
                    
                    accuracy = correctlyAnswered / totalAnswered
                    reporter.addToReport(correct, imageId, questionIds[idx], question, questionTypes[idx], answers[idx], prediction, accuracy, totalAnswered)
                    
                    if totalAnswered % saveAfter == 0:
                        reporter.saveReport()
                    
                    if totalAnswered % verbose == 0:
                        logger.info(f"Accuracy after {totalAnswered} questions: {round(accuracy, 5)}.")
                        
                    
                except Exception as e:
                    logger.error(f"An error occured: {e}. ImageID: {imageId}, QuestionID: {questionIds[idx]}, question: {question}, answer: {answers[idx]}.")
                    continue
