export interface ServicesParameters {
  [key: string]: null | number | string | boolean;
}

export interface AppendArgumentsResponse {
  text: string;
  parameters: ServicesParameters;
}

export interface AppendArgumentsRequest {
  text: string;
}
