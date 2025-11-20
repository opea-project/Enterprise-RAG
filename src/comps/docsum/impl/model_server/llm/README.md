# LLM Model Server for Document Summarization

This component utilizes the **LLM Microservice** for language model inference operations. The LLM microservice handles the core functionality of processing queries and documents to generate intelligent, context-aware responses.

For detailed information about the LLM microservice, including:
- Configuration options
- Supported model servers
- Setup and deployment instructions
- API documentation

Please refer to the [LLM Microservice README](../../../../llms/README.md).

> [!IMPORTANT]
> Docsum microservice uses OpenAI Client to connect to the LLM. Therefore, OpenAI API is required to run the pipeline correctly. To enable LLM with OpenAI API for streaming, run LLM with `LLM_OPENAI_FORMAT_STREAMING` set to `True`.

## Getting Started

To build and start all the services use Docker Compose

```bash
docker compose --env-file=.env -f docker-compose.yaml up --build -d
```

### Service Cleanup

To cleanup the services using Docker Compose:

```bash
docker compose -f docker-compose.yaml down
```

## Verify the Services

- Test the `llm-vllm-model-server` using the following command:
    ```bash
    curl http://localhost:8008/v1/completions \
        -X POST \
        -d '{"model": "meta-llama/Llama-3.1-8B-Instruct", "prompt": "What is Deep Learning?", "max_tokens": 32, "temperature": 0}' \
        -H "Content-Type: application/json"
    ```
    **NOTICE**: First ensure that the model server is operational. Warming up might take a while, and during this phase, the endpoint won't be ready to serve the query.

- Check the `llm-vllm-microservice` status:

    ```bash
    curl http://localhost:9000/v1/health_check \
        -X GET \
        -H 'Content-Type: application/json'
    ```

- Test the `llm-vllm-microservice` using the following command:
    ```bash
    curl http://localhost:9000/v1/chat/completions \
        -X POST \
        -d '{
                "messages": [
                      {
                        "role": "system",
                        "content": "### You are a helpful, respectful, and honest assistant to help the user with questions. Please refer to the search results obtained from the local knowledge base. Refer also to the conversation history if you think it is relevant to the current question. Ignore all information that you think is not relevant to the question. If you dont know the answer to a question, please dont share false information. ### Search results:  \n\n"
                      },
                      {
                        "role": "user",
                        "content": "### Question: What is Deep Learning? \n\n"
                      }
                    ],
                "max_new_tokens":32,
                "top_p":0.95,
                "temperature":0.01,
                "stream":false
            }' \
        -H 'Content-Type: application/json'
    ```

- Test the `docsum-microservice` using the following command:
    ```bash
    curl http://localhost:9001/v1/docsum \
        -X POST \
        -d '{
                "docs": [
                    {
                        "text": "Human history or world history is the record of humankind from prehistory to the present. Modern humans evolved in Africa around 300,000 years ago and initially lived as hunter-gatherers. They migrated out of Africa during the Last Ice Age and had spread across Earths continental land except Antarctica by the end of the Ice Age 12,000 years ago. Soon afterward, the Neolithic Revolution in West Asia brought the first systematic husbandry of plants and animals, and saw many humans transition from a nomadic life to a sedentary existence as farmers in permanent settlements. The growing complexity of human societies necessitated systems of accounting and writing. These developments paved the way for the emergence of early civilizations in Mesopotamia, Egypt, the Indus Valley, and China, marking the beginning of the ancient period in 3500 BCE. These civilizations supported the establishment of regional empires and acted as a fertile ground for the advent of transformative philosophical and religious ideas, initially Hinduism during the late Bronze Age, and – during the Axial Age: Buddhism, Confucianism, Greek philosophy, Jainism, Judaism, Taoism, and Zoroastrianism. The subsequent post-classical period, from about 500 to 1500 CE, witnessed the rise of Islam and the continued spread and consolidation of Christianity while civilization expanded to new parts of the world and trade between societies increased. These developments were accompanied by the rise and decline of major empires, such as the Byzantine Empire, the Islamic caliphates, the Mongol Empire, and various Chinese dynasties. This periods invention of gunpowder and of the printing press greatly affected subsequent history. During the early modern period, spanning from approximately 1500 to 1800 CE, European powers explored and colonized regions worldwide, intensifying cultural and economic exchange. This era saw substantial intellectual, cultural, and technological advances in Europe driven by the Renaissance, the Reformation in Germany giving rise to Protestantism, the Scientific Revolution, and the Enlightenment. By the 18th century, the accumulation of knowledge and technology had reached a critical mass that brought about the Industrial Revolution, substantial to the Great Divergence, and began the modern period starting around 1800 CE. The rapid growth in productive power further increased international trade and colonization, linking the different civilizations in the process of globalization, and cemented European dominance throughout the 19th century. Over the last 250 years, which included two devastating world wars, there has been a great acceleration in many spheres, including human population, agriculture, industry, commerce, scientific knowledge, technology, communications, military capabilities, and environmental degradation. The study of human history relies on insights from academic disciplines including history, archaeology, anthropology, linguistics, and genetics. To provide an accessible overview, researchers divide human history by a variety of periodizations."
                    }
                ],
                "summary_type": "refine"
            }' \
        -H 'Content-Type: application/json'
    ```
