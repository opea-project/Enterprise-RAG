FQDN: "${fqdn}"
huggingToken: "${hugging_face_token}"

%{ if llm_model_cpu != "" ~}
llm_model: "${llm_model_cpu}"
%{ endif ~}
%{ if llm_model_gaudi != "" ~}
llm_model_gaudi: "${llm_model_gaudi}"
%{ endif ~}
%{ if embedding_model_name != "" ~}
embedding_model_name: "${embedding_model_name}"
%{ endif ~}
%{ if reranking_model_name != "" ~}
reranking_model_name: "${reranking_model_name}"
%{ endif ~}

pipelines:
  - namespace: chatqa
    samplePath: chatqa/reference-${deployment_type}.yaml
    resourcesPath: chatqa/resources-reference-${deployment_type}.yaml
    modelConfigPath: chatqa/resources-model-${deployment_type}.yaml
    type: chatqa
