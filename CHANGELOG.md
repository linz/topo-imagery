# Changelog

## [3.0.1](https://github.com/linz/topo-imagery/compare/v3.0.0...v3.0.1) (2023-08-10)


### Bug Fixes

* gdalbuildvrt fails when coordinate system description is different TDE-818 ([#596](https://github.com/linz/topo-imagery/issues/596)) ([5758400](https://github.com/linz/topo-imagery/commit/575840018ced624ba8e4b179c7068b59461f975b))
* non-visual QA greyscale TDE-832 ([#593](https://github.com/linz/topo-imagery/issues/593)) ([afe25f3](https://github.com/linz/topo-imagery/commit/afe25f38c61ea671fa1942c1a1cdab9be3dba6f0))
* standardised path is not logged when non_visual_qa_passed ([#591](https://github.com/linz/topo-imagery/issues/591)) ([0c19104](https://github.com/linz/topo-imagery/commit/0c1910493a2952f21abe19d7d8df5ae5d43bcccf))
* stats are not written when retiling TDE-829 ([#599](https://github.com/linz/topo-imagery/issues/599)) ([c4bf5f2](https://github.com/linz/topo-imagery/commit/c4bf5f2fc78e66177b459b1e9482bc830b45a59a))


### Documentation

* comment to explain why extent is specified ([#584](https://github.com/linz/topo-imagery/issues/584)) ([1971bc2](https://github.com/linz/topo-imagery/commit/1971bc2a5d1cd85c7f26b6b424b01249686888b4))

## [3.0.0](https://github.com/linz/topo-imagery/compare/v2.2.1...v3.0.0) (2023-07-25)


### ⚠ BREAKING CHANGES

* standardise_validate should allow 1 output from multiple inputs TDE-784 ([#557](https://github.com/linz/topo-imagery/issues/557))

### Features

* standardise_validate allows passing a json file as input TDE-823 ([#564](https://github.com/linz/topo-imagery/issues/564)) ([ebd3e8e](https://github.com/linz/topo-imagery/commit/ebd3e8e00098d145371d8be240e9a97a7cffe2c1))
* standardise_validate should allow 1 output from multiple inputs TDE-784 ([#557](https://github.com/linz/topo-imagery/issues/557)) ([d0ddbbb](https://github.com/linz/topo-imagery/commit/d0ddbbba3d161f3e9249f45eaadd072d8b3810b8))


### Bug Fixes

* AREA_OR_POINT should be forced to AREA for DEMs TDE-787 ([#537](https://github.com/linz/topo-imagery/issues/537)) ([3b92a21](https://github.com/linz/topo-imagery/commit/3b92a21d070b9aabb77c6bbd27b7a9b646e97897))


### Reverts

* "revert: "chore: upgrade gdal from 3.6.1 to 3.7.0 ([#479](https://github.com/linz/topo-imagery/issues/479))" ([#536](https://github.com/linz/topo-imagery/issues/536))" ([#544](https://github.com/linz/topo-imagery/issues/544)) ([ca824f9](https://github.com/linz/topo-imagery/commit/ca824f91b57f4f245c9813928d4845f63fd9c1c6))

## [2.2.1](https://github.com/linz/topo-imagery/compare/v2.2.0...v2.2.1) (2023-07-12)


### Bug Fixes

* create a new release please PR to fix bug ([#548](https://github.com/linz/topo-imagery/issues/548)) ([c809721](https://github.com/linz/topo-imagery/commit/c8097217c318a04875d5918ce474552a4e4a3e93))

## [2.2.0](https://github.com/linz/topo-imagery/compare/v2.1.0...v2.2.0) (2023-07-12)


### Features

* handle standardising paletted tiffs ([#547](https://github.com/linz/topo-imagery/issues/547)) ([aa6ce05](https://github.com/linz/topo-imagery/commit/aa6ce05a7737f34bbaf5287e47e39e34474a01e7))


### Reverts

* "chore: upgrade gdal from 3.6.1 to 3.7.0 ([#479](https://github.com/linz/topo-imagery/issues/479))" ([#536](https://github.com/linz/topo-imagery/issues/536)) ([810b73c](https://github.com/linz/topo-imagery/commit/810b73c566e482b3caf29a73c1ffaccc32a6a1b4))

## [2.1.0](https://github.com/linz/topo-imagery/compare/v2.0.0...v2.1.0) (2023-07-04)


### Features

* add --producer-list to allow multiple producers TDE-781 ([#531](https://github.com/linz/topo-imagery/issues/531)) ([0a28d6f](https://github.com/linz/topo-imagery/commit/0a28d6f6f00deae2841d088f9b6a99bfdb437b14))
* add dem_lerc  preset TDE-779 ([#522](https://github.com/linz/topo-imagery/issues/522)) ([3e7378d](https://github.com/linz/topo-imagery/commit/3e7378d1506a5884b7151a29f6dd3a7281c3650a))


### Bug Fixes

* handle already existing collection JSON ([#532](https://github.com/linz/topo-imagery/issues/532)) ([7a26bae](https://github.com/linz/topo-imagery/commit/7a26bae03d8b2d9090cfb8dfb24d42473a0b2b62))
* standardising_validate.py fails when scale is 'None' ([#480](https://github.com/linz/topo-imagery/issues/480)) ([17296f1](https://github.com/linz/topo-imagery/commit/17296f1e0ffbb46d5160814ca6096d4c5893c996))


### Documentation

* add missing docstring ([#487](https://github.com/linz/topo-imagery/issues/487)) ([dd27c7c](https://github.com/linz/topo-imagery/commit/dd27c7c3f7209e58416e5e517498b0b68e7b3ca5))
* update docstring for tile_index.py ([#473](https://github.com/linz/topo-imagery/issues/473)) ([38ef275](https://github.com/linz/topo-imagery/commit/38ef275c304164c990675837cbba83076f80e512))
* update README release please instructions ([#496](https://github.com/linz/topo-imagery/issues/496)) ([d7369e0](https://github.com/linz/topo-imagery/commit/d7369e096b7d782e8f97bca10b6b384b70f33f89))
* update README.md ([#481](https://github.com/linz/topo-imagery/issues/481)) ([79add3c](https://github.com/linz/topo-imagery/commit/79add3cd3cd3fb8f5d75ba7a8ca2029145fd0b5a))

## [2.0.0](https://github.com/linz/topo-imagery/compare/v1.3.0...v2.0.0) (2023-04-18)


### ⚠ BREAKING CHANGES

* resume standardise validate TDE-710 ([#444](https://github.com/linz/topo-imagery/issues/444))

### Features

* fs.exists() checks if path exists TDE-710 ([#441](https://github.com/linz/topo-imagery/issues/441)) ([f79bd7a](https://github.com/linz/topo-imagery/commit/f79bd7a8b1ea7ef950479a3638595662f3417ed6))
* resume standardise validate TDE-710 ([#444](https://github.com/linz/topo-imagery/issues/444)) ([b4022a5](https://github.com/linz/topo-imagery/commit/b4022a509dc7d92e8d10eb384fa1b3408c45463e))


### Bug Fixes

* fs_local.write() fails when directory does not exist ([#445](https://github.com/linz/topo-imagery/issues/445)) ([935a041](https://github.com/linz/topo-imagery/commit/935a0419ee7c550793088c279e060d315bf8dad9))
* fs_s3.read() exceptions are not caught properly ([#432](https://github.com/linz/topo-imagery/issues/432)) ([3a855d5](https://github.com/linz/topo-imagery/commit/3a855d55f9a59bfe2d081835663b18b574380faa))
* unescaped bracket ([#426](https://github.com/linz/topo-imagery/issues/426)) ([f579638](https://github.com/linz/topo-imagery/commit/f57963854d0d3f61585055d2fbc5e3174f7948ea))

## [1.3.0](https://github.com/linz/topo-imagery/compare/v1.2.1...v1.3.0) (2023-03-29)


### Features

* deploy containers to ecr TDE-689 ([#408](https://github.com/linz/topo-imagery/issues/408)) ([31c713c](https://github.com/linz/topo-imagery/commit/31c713c9d5b7336f6af408e8a3bd6d592db9f831))


### Bug Fixes

* add latest to tag ([#416](https://github.com/linz/topo-imagery/issues/416)) ([82645ec](https://github.com/linz/topo-imagery/commit/82645ec3432b7f141a9f3af672b4d1aef2a46e68))
* add permissions ([#414](https://github.com/linz/topo-imagery/issues/414)) ([d05aa10](https://github.com/linz/topo-imagery/commit/d05aa1008eb51b8646f74fee675d56d4cbbfc9e9))
* update permissions ([#415](https://github.com/linz/topo-imagery/issues/415)) ([71c3fe9](https://github.com/linz/topo-imagery/commit/71c3fe9434209c2f87c333fe2323569a9d24d6a9))
* use multithreading for gdalwarp when creating COGS TDE-696 ([#399](https://github.com/linz/topo-imagery/issues/399)) ([061d3d6](https://github.com/linz/topo-imagery/commit/061d3d67bdb7a7385ffd84b0d060edde0010bd8c))

## [1.2.1](https://github.com/linz/topo-imagery/compare/v1.2.0...v1.2.1) (2023-03-08)


### Bug Fixes

* trailing char in local path is removed ([#389](https://github.com/linz/topo-imagery/issues/389)) ([604e591](https://github.com/linz/topo-imagery/commit/604e5911a7821d299cd6a2b5dc92176e4559a5eb))


### Documentation

* improve documentation about release process ([#362](https://github.com/linz/topo-imagery/issues/362)) ([d85653e](https://github.com/linz/topo-imagery/commit/d85653eec0ab254db15a86b1d3aad72a41e13083))

## [1.2.0](https://github.com/linz/topo-imagery/compare/v1.1.0...v1.2.0) (2023-03-01)


### Features

* make scale optional ([#372](https://github.com/linz/topo-imagery/issues/372)) ([20218bd](https://github.com/linz/topo-imagery/commit/20218bd3edc1af6113be1a917e6a7080525a5891))
* take source and target epsg, if not the same transform TDE-699 ([#375](https://github.com/linz/topo-imagery/issues/375)) ([547ec88](https://github.com/linz/topo-imagery/commit/547ec88871236c3df674d08a3f75c37c6c0e14c5))


### Bug Fixes

* be specific about nodata being None ([#363](https://github.com/linz/topo-imagery/issues/363)) ([8fe8211](https://github.com/linz/topo-imagery/commit/8fe82113d3f027e46364ecf33cd0ede5271c70ba))
* remove no data value (255) ensure is not none ([#360](https://github.com/linz/topo-imagery/issues/360)) ([a1154e8](https://github.com/linz/topo-imagery/commit/a1154e892053a6f15ef6b5c030d69ca261d95e39))

## [1.1.0](https://github.com/linz/topo-imagery/compare/v1.0.0...v1.1.0) (2023-02-15)


### Features

* add multiple STAC licensors TDE-643 ([#355](https://github.com/linz/topo-imagery/issues/355)) ([001b9fc](https://github.com/linz/topo-imagery/commit/001b9fc39264d062b302fe9cb15a89d1668066ca))

## [1.0.0](https://github.com/linz/topo-imagery/compare/v0.4.1...v1.0.0) (2023-02-13)


### ⚠ BREAKING CHANGES

* stac providers TDE-623 ([#348](https://github.com/linz/topo-imagery/issues/348))

### Features

* stac providers TDE-623 ([#348](https://github.com/linz/topo-imagery/issues/348)) ([9bc71a4](https://github.com/linz/topo-imagery/commit/9bc71a47492b9387acf337f738cad594f0c7586b))

## [0.4.1](https://github.com/linz/topo-imagery/compare/v0.4.0...v0.4.1) (2023-02-09)


### Features

* convert nodata to alpha TDE-625 ([#342](https://github.com/linz/topo-imagery/issues/342)) ([6710aea](https://github.com/linz/topo-imagery/commit/6710aea24306f5e651480e96215fdb447fe9aab8))


### Bug Fixes

* gdal info reference wrong file ([#347](https://github.com/linz/topo-imagery/issues/347)) ([52a2ee7](https://github.com/linz/topo-imagery/commit/52a2ee7354e939ed93b44f3b3d1d537e1d337d92))
* log wrong vsis3 path non visual qa TDE-563 ([#343](https://github.com/linz/topo-imagery/issues/343)) ([388ae19](https://github.com/linz/topo-imagery/commit/388ae1936782c6bf71b980efce9a739f2671c519))

## [0.4.0](https://github.com/linz/topo-imagery/compare/v0.3.0...v0.4.0) (2023-02-07)


### Features

* standardising 16bits TIFF TDE-628 ([#333](https://github.com/linz/topo-imagery/issues/333)) ([1a07683](https://github.com/linz/topo-imagery/commit/1a07683ece05da6dbafc46c03ca32f666e0e9627))


### Bug Fixes

* non visual qa errors logged twice TDE-563 ([#320](https://github.com/linz/topo-imagery/issues/320)) ([41c4c98](https://github.com/linz/topo-imagery/commit/41c4c98aa5ef0cfbf4bf28632bb07c1b5d398e9d))


### Documentation

* add versioning release section in readme ([#334](https://github.com/linz/topo-imagery/issues/334)) ([7ad502c](https://github.com/linz/topo-imagery/commit/7ad502c11c0ef8130beef3719fb0fb87852a16d8))

## [0.3.0](https://github.com/linz/topo-imagery/compare/v0.2.0...v0.3.0) (2023-01-19)


### Features

* add gray_webp preset TDE-482 ([#149](https://github.com/linz/topo-imagery/issues/149)) ([396dc16](https://github.com/linz/topo-imagery/commit/396dc16a5c6baf282c5f9c45ba994e7920b20a78))
* add standardising script (TDE-303) ([#23](https://github.com/linz/topo-imagery/issues/23)) ([fd60e53](https://github.com/linz/topo-imagery/commit/fd60e53eb8748c47cb27bf15270602562b7a8cf0))
* allow Create Polygons script to run with multiple files ([#48](https://github.com/linz/topo-imagery/issues/48)) ([8372cc7](https://github.com/linz/topo-imagery/commit/8372cc713d1cdd6d03cd629cc5c608d9bda24ba2))
* apply a cutline if supplied ([#240](https://github.com/linz/topo-imagery/issues/240)) ([13688d8](https://github.com/linz/topo-imagery/commit/13688d81e35ec86f267863f0b8619f75cb99e6f8))
* automatically refresh role assumptions ([#106](https://github.com/linz/topo-imagery/issues/106)) ([40e4b52](https://github.com/linz/topo-imagery/commit/40e4b52d303e693bfedb846e7d9e572609345926))
* cog output ([#60](https://github.com/linz/topo-imagery/issues/60)) ([38ef527](https://github.com/linz/topo-imagery/commit/38ef527b04061fb202985c9fedfe6eb73e47ac6e))
* create collection TDE-453 ([#177](https://github.com/linz/topo-imagery/issues/177)) ([20f5f34](https://github.com/linz/topo-imagery/commit/20f5f348222119e92cff2f45e7756ae668957688))
* create polygon script return temporary file path ([#47](https://github.com/linz/topo-imagery/issues/47)) ([34c210a](https://github.com/linz/topo-imagery/commit/34c210a6a1dc97d940998271dfe5f37f15d5d52b))
* create stac items TDE-452 ([#133](https://github.com/linz/topo-imagery/issues/133)) ([47e966a](https://github.com/linz/topo-imagery/commit/47e966a675f40a9da578fbbabb612f9dc0e672f1))
* create_polygons destination can be a full s3 path ([#15](https://github.com/linz/topo-imagery/issues/15)) ([d276baa](https://github.com/linz/topo-imagery/commit/d276baac6c204f65d1d06c27d5cd00b52091b58f))
* enable list source TDE-411 ([#36](https://github.com/linz/topo-imagery/issues/36)) ([c676b20](https://github.com/linz/topo-imagery/commit/c676b2031d080411ca66880b6811a135e1358497))
* File System Abstraction local/AWS TDE-407 ([#69](https://github.com/linz/topo-imagery/issues/69)) ([b4f035e](https://github.com/linz/topo-imagery/commit/b4f035e99bfe12ba8d72af6125ff2e05072dcf11))
* gdal concurrency TDE-457 ([#96](https://github.com/linz/topo-imagery/issues/96)) ([3f4a3be](https://github.com/linz/topo-imagery/commit/3f4a3bed092acee463cbdfed2efbc64d1c583cff))
* initialise collection stac TDE-453 ([#132](https://github.com/linz/topo-imagery/issues/132)) ([8c542d5](https://github.com/linz/topo-imagery/commit/8c542d547a0258115f886d5e7b38818f99e6850e))
* log pretty formatted gdalinfo in non visual qa logs TDE-563 ([#214](https://github.com/linz/topo-imagery/issues/214)) ([58d4cd2](https://github.com/linz/topo-imagery/commit/58d4cd27ea6348507fbf98a460dc43545a2ad9e2))
* log standardised image gdal virtual path when non visual qa error TDE-563 ([#239](https://github.com/linz/topo-imagery/issues/239)) ([e121df8](https://github.com/linz/topo-imagery/commit/e121df83acf044c80de5f945d030ff70eb8166eb))
* log the gdal version when run standardising TDE-559 ([#210](https://github.com/linz/topo-imagery/issues/210)) ([d458732](https://github.com/linz/topo-imagery/commit/d458732a5bc891d82568c483081e3dca5e94cbba))
* logs hostname and execution time TDE-431 ([#77](https://github.com/linz/topo-imagery/issues/77)) ([abb6634](https://github.com/linz/topo-imagery/commit/abb663435c670c2e3e7d87dccbf348366925806c))
* non visual qa log original tiff path TDE-563 ([#241](https://github.com/linz/topo-imagery/issues/241)) ([6320cc9](https://github.com/linz/topo-imagery/commit/6320cc94d8ee9ae6c86a18a5986233e27187575a))
* Non Visual QA script (TDE-309) ([#40](https://github.com/linz/topo-imagery/issues/40)) ([8411779](https://github.com/linz/topo-imagery/commit/8411779a6bb8875e3c17268587cfbe1ee264af4c))
* optimise cutline handling by only using the cutline if required ([#258](https://github.com/linz/topo-imagery/issues/258)) ([5000a65](https://github.com/linz/topo-imagery/commit/5000a65f7516a9a934fdd0937a71d1f5aeebf2b4))
* rename tiff file if not aligned with its tile name TDE-497 ([#209](https://github.com/linz/topo-imagery/issues/209)) ([7e547d6](https://github.com/linz/topo-imagery/commit/7e547d6deee18355f64703f39026087e8401b9f3))
* run standardising step on a list of files (TDE-412) ([#35](https://github.com/linz/topo-imagery/issues/35)) ([c119a56](https://github.com/linz/topo-imagery/commit/c119a561ed1cb1830f85f67a4152d37df963dd5e))
* standardise following by non visual QA check TDE-450 ([#90](https://github.com/linz/topo-imagery/issues/90)) ([ee8227d](https://github.com/linz/topo-imagery/commit/ee8227d074c87981e2b3c776364e7c79824f1ad0))
* switch between two gdal presets "lzw" or "webp" ([#108](https://github.com/linz/topo-imagery/issues/108)) ([9483f51](https://github.com/linz/topo-imagery/commit/9483f51ac81fcae3e2d57dd5278c3f3ae7141e4f))
* tde-421 remove destination arguments ([#61](https://github.com/linz/topo-imagery/issues/61)) ([ba69fea](https://github.com/linz/topo-imagery/commit/ba69fea3df9cafe01c57a7564f0e4c16f6d2fc08))
* update stac collection TDE-453 ([#134](https://github.com/linz/topo-imagery/issues/134)) ([9127002](https://github.com/linz/topo-imagery/commit/9127002151b664235de548aa87492849b798187b))
* upgrade to stable GDAL v3.6 TDE-565 ([#217](https://github.com/linz/topo-imagery/issues/217)) ([786b11e](https://github.com/linz/topo-imagery/commit/786b11e6e53eba821fd2a1e1375153a595e059ee))
* use a fixed version of osgeo/gdal container TDE-555 ([#204](https://github.com/linz/topo-imagery/issues/204)) ([e6837ec](https://github.com/linz/topo-imagery/commit/e6837ec7de37239585c39d6b1b7a17d9dffe588b))
* write processed file paths in tmp/file_list.json ([#50](https://github.com/linz/topo-imagery/issues/50)) ([5387093](https://github.com/linz/topo-imagery/commit/5387093c3707ed3601ef7a135a105259634a121b))


### Bug Fixes

* --cutline is not required ([#244](https://github.com/linz/topo-imagery/issues/244)) ([9fcb901](https://github.com/linz/topo-imagery/commit/9fcb9011774a09014cc7cc3ed76db88f39d992d5))
* a couple of bugs in get_session_credentials ([#120](https://github.com/linz/topo-imagery/issues/120)) ([d6372e7](https://github.com/linz/topo-imagery/commit/d6372e7bd6ede4a178e598cf4ef97e11c1803a54))
* accept preset arg standardise-validate ([#119](https://github.com/linz/topo-imagery/issues/119)) ([aa86be8](https://github.com/linz/topo-imagery/commit/aa86be85b82583cd5c337b24f6be2f80f0e37d06))
* add 'certifi' lib to temporary fix poetry install issue TDE-451 ([#88](https://github.com/linz/topo-imagery/issues/88)) ([0dd3ea7](https://github.com/linz/topo-imagery/commit/0dd3ea77e0f8b40e19010b50b65476b1c653814e))
* append to a temporary command list ([#110](https://github.com/linz/topo-imagery/issues/110)) ([6527603](https://github.com/linz/topo-imagery/commit/6527603c2a780f2c7fe3248be13a497062bc3b88))
* argument source was not correctly set ([#49](https://github.com/linz/topo-imagery/issues/49)) ([44ff66f](https://github.com/linz/topo-imagery/commit/44ff66f62586d3c3beb99360e17908a386e596e9))
* boto3 sessions need to create resources not clients ([#245](https://github.com/linz/topo-imagery/issues/245)) ([3cee053](https://github.com/linz/topo-imagery/commit/3cee053667de9659d2297429ea588fed6ef1c7f0))
* collection title escaped unicode TDE-594 ([#288](https://github.com/linz/topo-imagery/issues/288)) ([a679042](https://github.com/linz/topo-imagery/commit/a679042707511e4e2fdd656a91ebc49d92a16093))
* correct type imports ([#261](https://github.com/linz/topo-imagery/issues/261)) ([78e55eb](https://github.com/linz/topo-imagery/commit/78e55ebef8515881c37090b53079569c0d34fafc))
* download sidecar files like tfw and prj ([#246](https://github.com/linz/topo-imagery/issues/246)) ([b8bb95a](https://github.com/linz/topo-imagery/commit/b8bb95adc0ed18c25bebe1aaac1146b88e12aba0))
* Elastic Search is expecting an object in 'source' ([#156](https://github.com/linz/topo-imagery/issues/156)) ([8b9503b](https://github.com/linz/topo-imagery/commit/8b9503b10527b64074ef7ff28f7378a47bac0c5d))
* force a alpha band on all imagery if a cutline is present ([#264](https://github.com/linz/topo-imagery/issues/264)) ([dab4565](https://github.com/linz/topo-imagery/commit/dab4565ca058a857865f96bf88eff83bb10b63cb))
* GDAL error was not logged when command run fails ([#52](https://github.com/linz/topo-imagery/issues/52)) ([01d941e](https://github.com/linz/topo-imagery/commit/01d941e0895f47b20560c4b1b8b69f5a007822c7))
* geometry, bbox and asset type TDE-502 TDE-520 ([#185](https://github.com/linz/topo-imagery/issues/185)) ([0229df8](https://github.com/linz/topo-imagery/commit/0229df85f81714407cbbc15727b856de612f23b1))
* keep temporary files so they are pushed to the artifact bucket ([#66](https://github.com/linz/topo-imagery/issues/66)) ([86b8c3a](https://github.com/linz/topo-imagery/commit/86b8c3ae49de908a16e7e8907bd78729b354326f))
* log gdal stderr instead of raising an exception TDE-557 ([#203](https://github.com/linz/topo-imagery/issues/203)) ([4032145](https://github.com/linz/topo-imagery/commit/4032145b32b1bacceb721d9ad336ed678e6094af))
* log Non Visual QA error report in a JSON format ([#55](https://github.com/linz/topo-imagery/issues/55)) ([ed4d623](https://github.com/linz/topo-imagery/commit/ed4d623ad3894722f4e6a27455e8af3451efdde2))
* make cutline value optional TDE-602 ([#292](https://github.com/linz/topo-imagery/issues/292)) ([cfa20cf](https://github.com/linz/topo-imagery/commit/cfa20cff9a70baf2713518a5f3781aa18e8db995))
* not logging source as a list of string ([#116](https://github.com/linz/topo-imagery/issues/116)) ([a871935](https://github.com/linz/topo-imagery/commit/a8719359a874f2f654d1ed09d7e1b4c69dbf10c2))
* release-please.yml fails prettier ([#307](https://github.com/linz/topo-imagery/issues/307)) ([330fa04](https://github.com/linz/topo-imagery/commit/330fa04c609f4996bac1c77701aaca5305ed1f45))
* retry upto 3 times when InvalidIdentityTokenException happens ([#115](https://github.com/linz/topo-imagery/issues/115)) ([e27f2d0](https://github.com/linz/topo-imagery/commit/e27f2d0db836caf1cd8fc2c24f435f5fd766adc0))
* skip files which are not tiff ([#53](https://github.com/linz/topo-imagery/issues/53)) ([90396a6](https://github.com/linz/topo-imagery/commit/90396a6347d931f1f5e1c3abd16ae1ff6f86ea28))
* skip non visual qa if no file has been standardised ([#97](https://github.com/linz/topo-imagery/issues/97)) ([25a85c1](https://github.com/linz/topo-imagery/commit/25a85c1fbc8794bc410760577af051cc285ef079))
* specify and check bands TDE-533 ([#196](https://github.com/linz/topo-imagery/issues/196)) ([d4e512f](https://github.com/linz/topo-imagery/commit/d4e512fa3e91c7daaacd4348763d494933c5c6d3))
* support 1 band palleted grey scale TDE-601 ([#269](https://github.com/linz/topo-imagery/issues/269)) ([d2327a0](https://github.com/linz/topo-imagery/commit/d2327a0c8507d044c962c34b87b3ea33168941e2))
* suppress aux xml file creation ([#121](https://github.com/linz/topo-imagery/issues/121)) ([c674366](https://github.com/linz/topo-imagery/commit/c674366a7062c81271830975cc3b750b2fafa82d))
* TDE-454 remove `standardise` from file name ([#92](https://github.com/linz/topo-imagery/issues/92)) ([099df34](https://github.com/linz/topo-imagery/commit/099df340ce6bb00ae199524893f5f3ef8a62350d))
* tidy up geometry and bbox TDE-522 ([#227](https://github.com/linz/topo-imagery/issues/227)) ([02b06b5](https://github.com/linz/topo-imagery/commit/02b06b51a58650ffbe1a18a4bedd4996251c6c16))
* use $AWS_ROLE_CONFIG_PATH to be consistent ([#109](https://github.com/linz/topo-imagery/issues/109)) ([d1fff0d](https://github.com/linz/topo-imagery/commit/d1fff0d7be08a5475f99d7fa85e3489fe69469a2))
