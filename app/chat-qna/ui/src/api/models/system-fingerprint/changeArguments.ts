interface ServiceArgumentsToChange {
  name: string;
  data: {
    [argumentName: string]: string | number | boolean | null;
  };
}

export type ChangeArgumentsRequestBody = ServiceArgumentsToChange[];
